import time
from vpn.config import config

class RekeyPolicy:
    """
    Tracks per-session packet counts and elapsed time.
    Call should_rekey() after every encrypted packet. When it returns True,
    initiate a new handshake for this session.
    
    Usage:
        policy = RekeyPolicy()
        policy.reset()
        ...
        if policy.should_rekey(packets_sent):
            # trigger renegotiation
    """

    def __init__(
        self,
        max_packets: int = None,
        max_seconds: int = None
    ):
        self.max_packets = max_packets or config.rekey_after_packets
        self.max_seconds = max_seconds or config.rekey_after_seconds
        self._start_time: float = time.time()
        self._packet_count: int = 0

    def reset(self) -> None:
        self._start_time = time.time()
        self._packet_count = 0

    def tick(self) -> None:
        """Call once per sent or received packet."""
        self._packet_count += 1

    def should_rekey(self) -> bool:
        elapsed = time.time() - self._start_time
        return (
            self._packet_count >= self.max_packets
            or elapsed >= self.max_seconds
        )

    @property
    def packets_since_rekey(self) -> int:
        return self._packet_count

    @property
    def seconds_since_rekey(self) -> float:
        return time.time() - self._start_time
