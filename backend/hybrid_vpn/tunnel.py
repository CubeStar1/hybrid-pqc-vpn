"""Linux TUN device management and encrypted UDP tunnel transport.

Phase 2: UDP framing with AES-256-GCM encryption and sequence-number replay protection.
Phase 3: TUN creation via /dev/net/tun, IP/route management via pyroute2.

All Linux-specific operations are guarded so the module can be imported on any OS;
calling the actual tunnel functions on non-Linux raises a clear RuntimeError.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
import struct
import threading
from dataclasses import dataclass, field

from .crypto.classical import aes_gcm_decrypt, aes_gcm_encrypt

logger = logging.getLogger(__name__)

IS_LINUX = platform.system() == "Linux"

# ioctl constants for TUN device creation (Linux only)
TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

# Packet frame layout: [4-byte sequence][encrypted payload + 16-byte GCM tag]
SEQ_SIZE = 4
MAX_PACKET = 2048


def _require_linux(operation: str) -> None:
    if not IS_LINUX:
        raise RuntimeError(f"{operation} requires Linux (current: {platform.system()})")


# ── TUN device ───────────────────────────────────────────────────────


@dataclass
class TunDevice:
    """Manages a Linux TUN network interface."""

    name: str = "hyb0"
    mtu: int = 1280
    _fd: int | None = field(default=None, init=False, repr=False)

    def open(self) -> str:
        """Create the TUN device. Returns the actual interface name."""
        _require_linux("TUN device creation")
        import fcntl

        self._fd = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack("16sH", self.name.encode(), IFF_TUN | IFF_NO_PI)
        result = fcntl.ioctl(self._fd, TUNSETIFF, ifr)
        self.name = result[:16].strip(b"\x00").decode()
        logger.info("TUN device %s opened (fd=%d)", self.name, self._fd)
        return self.name

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            logger.info("TUN device %s closed", self.name)
            self._fd = None

    def read(self, size: int = MAX_PACKET) -> bytes:
        if self._fd is None:
            raise RuntimeError("TUN device not open")
        return os.read(self._fd, size)

    def write(self, data: bytes) -> int:
        if self._fd is None:
            raise RuntimeError("TUN device not open")
        return os.write(self._fd, data)

    @property
    def is_open(self) -> bool:
        return self._fd is not None


# ── Interface configuration (pyroute2) ───────────────────────────────


def configure_tun(name: str, address: str, prefixlen: int, mtu: int) -> None:
    """Assign IP address, set MTU, and bring the TUN interface up."""
    _require_linux("TUN configuration")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        idx = ipr.link_lookup(ifname=name)
        if not idx:
            raise RuntimeError(f"Interface {name} not found")
        idx = idx[0]
        ipr.link("set", index=idx, mtu=mtu)
        ipr.addr("add", index=idx, address=address, prefixlen=prefixlen)
        ipr.link("set", index=idx, state="up")
    logger.info("Configured %s: %s/%d mtu=%d UP", name, address, prefixlen, mtu)


def add_route(destination: str, prefixlen: int, device: str) -> None:
    """Add a route through the specified device."""
    _require_linux("Route management")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        idx = ipr.link_lookup(ifname=device)
        if not idx:
            raise RuntimeError(f"Interface {device} not found")
        ipr.route("add", dst=f"{destination}/{prefixlen}", oif=idx[0])
    logger.info("Route added: %s/%d via %s", destination, prefixlen, device)


def teardown_tun(name: str) -> None:
    """Bring down a TUN interface."""
    _require_linux("TUN teardown")
    from pyroute2 import IPRoute

    with IPRoute() as ipr:
        idx = ipr.link_lookup(ifname=name)
        if idx:
            ipr.link("set", index=idx[0], state="down")
    logger.info("Interface %s brought down", name)


# ── Encrypted UDP transport ──────────────────────────────────────────


@dataclass
class UdpTransport:
    """AES-256-GCM encrypted UDP datagram transport with replay protection."""

    key: bytes  # 32-byte AES-256 key
    local_port: int
    remote_addr: tuple[str, int]
    _sock: socket.socket | None = field(default=None, init=False, repr=False)
    _send_seq: int = field(default=0, init=False, repr=False)
    _recv_window: int = field(default=0, init=False, repr=False)

    def bind(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", self.local_port))
        self._sock.settimeout(0.5)  # non-blocking with short timeout for clean shutdown
        logger.info("UDP transport bound on :%d → %s:%d", self.local_port, *self.remote_addr)

    def close(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    def send(self, plaintext: bytes) -> None:
        """Encrypt and send a packet."""
        if not self._sock:
            raise RuntimeError("UDP transport not bound")

        self._send_seq += 1
        # 12-byte nonce: 4-byte seq number + 8 zero bytes
        nonce = self._send_seq.to_bytes(SEQ_SIZE, "big") + b"\x00" * 8
        ciphertext = aes_gcm_encrypt(self.key, nonce, plaintext)
        frame = self._send_seq.to_bytes(SEQ_SIZE, "big") + ciphertext
        self._sock.sendto(frame, self.remote_addr)

    def recv(self) -> bytes | None:
        """Receive and decrypt a packet. Returns None on timeout or invalid packet."""
        if not self._sock:
            raise RuntimeError("UDP transport not bound")

        try:
            data, _ = self._sock.recvfrom(MAX_PACKET + SEQ_SIZE + 16)
        except (TimeoutError, OSError):
            return None

        if len(data) < SEQ_SIZE + 16:  # seq + minimum GCM tag
            return None

        seq = int.from_bytes(data[:SEQ_SIZE], "big")

        # Basic replay protection: reject packets with seq ≤ last received
        if seq <= self._recv_window:
            logger.warning("Replay detected: seq=%d, window=%d", seq, self._recv_window)
            return None
        self._recv_window = seq

        nonce = seq.to_bytes(SEQ_SIZE, "big") + b"\x00" * 8
        try:
            return aes_gcm_decrypt(self.key, nonce, data[SEQ_SIZE:])
        except Exception:
            logger.warning("Decryption failed for seq=%d", seq)
            return None


# ── Tunnel manager (TUN ↔ UDP forwarding) ────────────────────────────


class TunnelManager:
    """Orchestrates the full tunnel lifecycle: TUN device + encrypted UDP transport.

    Call start() to open the TUN, bind UDP, and begin forwarding in background threads.
    Call stop() to cleanly tear everything down.
    """

    def __init__(
        self,
        tun_name: str,
        tun_address: str,
        tun_prefixlen: int,
        tun_mtu: int,
        udp_key: bytes,
        udp_local_port: int,
        udp_remote_addr: tuple[str, int],
    ) -> None:
        self.tun = TunDevice(name=tun_name, mtu=tun_mtu)
        self.udp = UdpTransport(key=udp_key, local_port=udp_local_port, remote_addr=udp_remote_addr)
        self._address = tun_address
        self._prefixlen = tun_prefixlen
        self._running = False
        self._threads: list[threading.Thread] = []
        self._stats = {"packets_sent": 0, "packets_recv": 0, "bytes_sent": 0, "bytes_recv": 0}

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Open TUN, configure interface, bind UDP, start forwarding."""
        _require_linux("Tunnel start")

        self.tun.open()
        configure_tun(self.tun.name, self._address, self._prefixlen, self.tun.mtu)
        self.udp.bind()

        self._running = True
        t_out = threading.Thread(target=self._forward_tun_to_udp, name="tun→udp", daemon=True)
        t_in = threading.Thread(target=self._forward_udp_to_tun, name="udp→tun", daemon=True)
        self._threads = [t_out, t_in]
        t_out.start()
        t_in.start()
        logger.info("Tunnel started: %s (%s/%d) ↔ UDP :%d", self.tun.name, self._address, self._prefixlen, self.udp.local_port)

    def stop(self) -> None:
        """Stop forwarding, tear down TUN and UDP."""
        self._running = False
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()

        self.udp.close()
        try:
            teardown_tun(self.tun.name)
        except Exception:
            pass
        self.tun.close()
        logger.info("Tunnel stopped")

    def _forward_tun_to_udp(self) -> None:
        """Read IP packets from TUN → encrypt → send over UDP."""
        while self._running:
            try:
                packet = self.tun.read()
                if packet:
                    self.udp.send(packet)
                    self._stats["packets_sent"] += 1
                    self._stats["bytes_sent"] += len(packet)
            except OSError:
                if self._running:
                    logger.exception("Error reading from TUN")
                break

    def _forward_udp_to_tun(self) -> None:
        """Receive UDP packets → decrypt → write to TUN."""
        while self._running:
            packet = self.udp.recv()
            if packet:
                try:
                    self.tun.write(packet)
                    self._stats["packets_recv"] += 1
                    self._stats["bytes_recv"] += len(packet)
                except OSError:
                    if self._running:
                        logger.exception("Error writing to TUN")
                    break
