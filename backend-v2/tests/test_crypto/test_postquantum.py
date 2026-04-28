from vpn.crypto.postquantum import (
    mlkem_generate_keypair, mlkem_encapsulate, mlkem_decapsulate,
    mldsa_generate_keypair, mldsa_sign, mldsa_verify
)

def test_mlkem_encap_decap_roundtrip():
    """The shared secret from encapsulate must match decapsulate."""
    priv, pub = mlkem_generate_keypair()
    ciphertext, ss_encap = mlkem_encapsulate(pub)
    ss_decap = mlkem_decapsulate(priv, ciphertext)
    assert ss_encap == ss_decap

def test_mlkem_wrong_private_key_gives_different_secret():
    _, pub = mlkem_generate_keypair()
    wrong_priv, _ = mlkem_generate_keypair()
    ct, ss_real = mlkem_encapsulate(pub)
    ss_wrong = mlkem_decapsulate(wrong_priv, ct)
    assert ss_real != ss_wrong

def test_mldsa_sign_verify_roundtrip():
    priv, pub = mldsa_generate_keypair()
    msg = b"post-quantum signature test"
    sig = mldsa_sign(priv, msg)
    assert mldsa_verify(pub, msg, sig) is True

def test_mldsa_rejects_tampered_message():
    priv, pub = mldsa_generate_keypair()
    sig = mldsa_sign(priv, b"original")
    assert mldsa_verify(pub, b"different", sig) is False
