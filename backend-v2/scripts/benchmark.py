"""
Benchmark: classical vs hybrid handshake latency.
Run: python scripts/benchmark.py [--iterations N]
"""
import sys, time, statistics, argparse
import os

# Add parent directory to path to allow imports from vpn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vpn.handshake.initiator import HandshakeInitiator
from vpn.handshake.responder import HandshakeResponder

def run_handshake() -> float:
    initiator = HandshakeInitiator()
    responder = HandshakeResponder()
    t0 = time.perf_counter()
    hello = initiator.create_hello()
    response = responder.process_hello(hello)
    finish = initiator.process_response(response)
    responder.process_finish(finish)
    return (time.perf_counter() - t0) * 1000

def benchmark(n: int):
    print(f"Running {n} hybrid handshakes...")
    times = [run_handshake() for _ in range(n)]
    print(f"\n{'Suite':<45} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    print("-" * 85)
    label = "X25519 + ML-KEM-768 + ECDSA + ML-DSA (hybrid)"
    print(
        f"{label:<45} "
        f"{statistics.mean(times):>7.2f}ms "
        f"{statistics.stdev(times) if n > 1 else 0:>7.2f}ms "
        f"{min(times):>7.2f}ms "
        f"{max(times):>7.2f}ms"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()
    benchmark(args.iterations)
