from hybrid_vpn.crypto.hybrid import derive_hybrid_traffic_secrets


def test_hybrid_key_schedule_separates_directional_keys():
    traffic = derive_hybrid_traffic_secrets(
        ecdh_shared_secret=b"\x01" * 32,
        pqc_shared_secret=b"\x02" * 32,
        transcript_digest=b"\x03" * 32,
    )
    assert traffic.client_key != traffic.server_key
    assert traffic.client_nonce_base != traffic.server_nonce_base
