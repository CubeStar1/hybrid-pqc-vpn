from vpn.config import config

KNOWN_SUITES = {
    "X25519+MLKEM768+AESGCM+ECDSA+MLDSA",
    "X25519+AESGCM+ECDSA",
}

def negotiate_suite(initiator_suites: list[str]) -> str | None:
    """
    Server-side: pick the first suite from initiator's list that we support.
    Returns the selected suite string or None if no common suite.
    """
    our_suites = set(config.supported_algo_suites)
    for suite in initiator_suites:
        if suite in our_suites and suite in KNOWN_SUITES:
            return suite
    return None

def is_hybrid_suite(suite: str) -> bool:
    return "MLKEM" in suite and "MLDSA" in suite

def is_classical_suite(suite: str) -> bool:
    return "MLKEM" not in suite
