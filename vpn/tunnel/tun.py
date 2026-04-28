import os
try:
    import fcntl
except ImportError:
    fcntl = None
import struct
import asyncio
from vpn.config import config

# ioctl constants for Linux TUN/TAP
TUNSETIFF = 0x400454CA
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000    # No packet information header

class TunInterface:
    """
    Manages a Linux TUN interface.
    Must be opened as root or with CAP_NET_ADMIN.
    
    Usage:
        tun = TunInterface()
        tun.open()
        # configure IP: ip addr add 10.0.0.1/24 dev vpn0
        # bring up:     ip link set vpn0 up
        raw_packet = await tun.read()
        await tun.write(raw_packet)
        tun.close()
    """

    def __init__(self, name: str = None, mtu: int = None):
        self.name = name or config.tun_name
        self.mtu = mtu or config.tun_mtu
        self._fd: int | None = None

    def open(self) -> None:
        """Opens /dev/net/tun and creates the named TUN interface."""
        if fcntl is None:
            raise OSError("TunInterface only supported on Linux (fcntl required)")
            
        self._fd = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack("16sH", self.name.encode(), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self._fd, TUNSETIFF, ifr)
        # Set non-blocking for asyncio compatibility
        flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        fcntl.fcntl(self._fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    async def read(self) -> bytes:
        """Async read of one IP packet from the TUN interface."""
        if self._fd is None:
            raise OSError("TUN interface not open")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, os.read, self._fd, self.mtu + 4)

    async def write(self, packet: bytes) -> None:
        """Async write of one IP packet to the TUN interface."""
        if self._fd is None:
            raise OSError("TUN interface not open")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.write, self._fd, packet)
