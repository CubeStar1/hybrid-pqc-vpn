from fastapi import APIRouter
from api.schemas.models import HandshakeMetrics
from vpn.handshake.initiator import HandshakeInitiator
from vpn.handshake.responder import HandshakeResponder
import time, statistics

router = APIRouter(prefix="/metrics", tags=["metrics"])

def _run_handshake_timed(suite_preference: list[str]) -> float:
    """Returns handshake duration in milliseconds."""
    # Temporarily override config for this measurement
    # (In a real implementation, we'd pass the suite to the constructor)
    # For now, using the local handshake simulation
    
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()
    
    start = time.perf_counter()
    hello = initiator.create_hello()
    # Mocking suite preference if needed, though initiator currently takes from config
    response = responder.process_hello(hello)
    finish = initiator.process_response(response)
    responder.process_finish(finish)
    end = time.perf_counter()
    
    return (end - start) * 1000  # convert to ms


@router.get("/handshake", response_model=list[HandshakeMetrics])
async def handshake_benchmark(iterations: int = 20):
    """
    Runs N hybrid handshakes and returns latency statistics.
    Use ?iterations=50 for production benchmarking.
    """
    results = []
    
    hybrid_times = [_run_handshake_timed(["X25519+MLKEM768+AESGCM+ECDSA+MLDSA"]) for _ in range(iterations)]
    results.append(HandshakeMetrics(
        suite="X25519+MLKEM768+AESGCM+ECDSA+MLDSA",
        iterations=iterations,
        mean_ms=statistics.mean(hybrid_times),
        std_ms=statistics.stdev(hybrid_times) if iterations > 1 else 0,
        min_ms=min(hybrid_times),
        max_ms=max(hybrid_times),
    ))
    
    return results
