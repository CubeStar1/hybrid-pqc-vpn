# CNS Lab EL

## 1. Introduction

### What is a VPN?

A Virtual Private Network (VPN) creates an encrypted “tunnel” over an untrusted network (typically the public Internet) so that a client device can communicate securely with a remote network or service.

- **Confidentiality:** outsiders cannot read the traffic.
- **Integrity:** outsiders cannot silently modify traffic.
- **Authentication:** the client verifies the server (and often vice versa).
- **Access control:** the VPN becomes a controlled entry point into a private network.

In practice, a VPN system usually combines:

- A **tunnel protocol** (how packets are encapsulated and transported)
- A **handshake/key exchange** (how both sides agree on keys)
- **Symmetric encryption** (fast bulk encryption of data)
- **Authentication** (identity verification and protection against active attackers)

### What is hybrid cryptography?

Hybrid cryptography combines **two different cryptographic families** to achieve stronger security properties than either alone.

In the context of “classical + post-quantum” security, *hybrid cryptography* typically means:

- Run a **classical** key exchange (e.g., ECDH) and a **post-quantum** key exchange (e.g., Kyber/ML-KEM).
- Combine the resulting secrets using a **Key Derivation Function (KDF)** such as HKDF.
- Use the derived key(s) for symmetric encryption (AES-GCM or ChaCha20-Poly1305).

The goal is that the final session keys remain secure if **at least one** of the component key exchanges remains secure.

### Why is post-quantum security needed?

Many widely deployed public-key algorithms rely on mathematical problems that are hard for classical computers but are expected to be efficiently solvable by sufficiently large quantum computers.

Key quantum threats:

- **Shor’s algorithm:** would break RSA and Elliptic Curve Cryptography (ECC) by efficiently factoring integers (RSA) and solving the discrete logarithm problem (ECC). This directly threatens common VPN building blocks such as RSA/ECDSA certificates and ECDH key exchange.
- **“Harvest now, decrypt later” (HNDL):** an attacker can record encrypted traffic today and store it. If they later obtain a quantum computer (or other future capability), they can decrypt the historical traffic *if the key establishment used quantum-vulnerable algorithms*.

Why this matters for VPNs:

- VPN traffic often includes **long-lived sensitive data** (intellectual property, government data, health data).
- Even if you rotate keys frequently, recorded sessions may become decryptable later if the handshake can be broken retroactively.
- Post-quantum key exchange aims to protect session key establishment against quantum adversaries.

---

## 2. Core Concept of a Hybrid VPN

### How classical and post-quantum cryptography are combined

A hybrid VPN keeps the familiar VPN structure (tunnel + handshake + data encryption), but changes the handshake to include:

- A **classical Key Encapsulation / Key Agreement** component (typically **ECDH**) and
- A **post-quantum KEM** component (typically **Kyber / ML-KEM**)

Then, both outputs are mixed together using a KDF.

A typical pattern:

- $s_{ecdh}$ = shared secret from ECDH
- $s_{pqc}$ = shared secret from PQC KEM
- Session key = HKDF( $s_{ecdh} || s_{pqc}$ , transcript)

### Hybrid key exchange (clear explanation)

A simple way to understand hybrid key exchange is:

1. The client and server perform **two independent exchanges**.
2. Each exchange yields a secret that an attacker should not be able to compute.
3. The secrets are **combined** so that breaking only one exchange is not enough.

Two common combination strategies:

- **Concatenate then KDF:** `HKDF( s_ecdh || s_pqc, info=handshake_transcript )`
- **Extract-then-expand with multiple inputs:** `HKDF-Extract(salt, s_ecdh)`, then mix in `s_pqc` (or vice versa)

In either case, a KDF is used to:

- Produce fixed-length symmetric keys
- Bind keys to the handshake transcript (protect against some downgrade/mitm manipulations)
- Ensure good randomness even if one component secret is weak

### Why combining both improves security

Hybrid designs aim for “**at least one survives**” security:

- If **ECDH** is broken by quantum computers in the future but **Kyber/ML-KEM** remains secure, the session keys still remain secure.
- If a PQC algorithm is later found to have weaknesses, **ECDH** still provides security against classical attackers today.

This is particularly valuable during the transition period where:

- PQC is still relatively new (less time-tested than ECC), and
- Quantum risk is increasing, but timelines and capabilities are uncertain.

---

## 3. Architecture of a Hybrid VPN

A hybrid VPN can be implemented by extending an existing VPN handshake (or designing a new one) to support a hybrid key schedule.

### Main components

#### Tunnel protocol

The tunnel protocol defines how traffic is carried once keys are established.

- **WireGuard:** modern, lean design, uses Noise-based handshakes; widely studied.
- **OpenVPN:** TLS-based; flexible and mature.
- **IPsec/IKEv2:** standards-based, widely deployed in enterprises.

Hybrid concepts apply to all of them, but the integration points differ:

- WireGuard/Noise: hybridize the **Noise handshake**.
- OpenVPN/TLS: hybridize the **TLS handshake** or use hybrid ciphersuites.
- IPsec/IKE: hybridize the **IKE key exchange**.

#### Classical key exchange (ECDH)

- Uses elliptic curves (e.g., P-256, X25519)
- Produces a shared secret $s_{ecdh}$
- Efficient and well-understood
- Vulnerable to Shor’s algorithm on large quantum computers

#### Post-quantum key exchange (Kyber / ML-KEM)

- Typically implemented as a **KEM (Key Encapsulation Mechanism)**.
- One party publishes a PQ public key; the other encapsulates to it.
- Produces a shared secret $s_{pqc}$ and a ciphertext that must be transmitted.

Note on naming:

- **Kyber** is the original NIST PQC KEM finalist/winner.
- **ML-KEM** is the standardized name (Module-Lattice KEM) derived from Kyber.

#### Key derivation (HKDF)

HKDF (HMAC-based Key Derivation Function) turns raw shared secrets into cryptographic keys.

- **HKDF-Extract:** converts input key material to a pseudorandom key (PRK)
- **HKDF-Expand:** derives multiple keys (encryption keys, IVs, rekey keys)

HKDF is used so that:

- Keys are uniformly distributed
- Keys are context-bound (via `info` strings and transcript)
- You can derive many keys from one master secret safely

#### Symmetric encryption (AES / ChaCha20)

Data-plane traffic uses fast symmetric encryption:

- **AES-GCM:** hardware-accelerated on many CPUs; common in enterprise settings
- **ChaCha20-Poly1305:** performs well on devices without AES acceleration; widely used in modern protocols

The hybrid aspect is not in the symmetric cipher itself, but in how the symmetric keys are established.

#### Authentication (RSA/ECDSA + Dilithium)

Authentication proves identity and prevents active attackers from impersonating the VPN server.

Two approaches:

1. **Hybrid authentication:** use both a classical signature and a PQ signature.
    - Classical: **RSA** or **ECDSA**
    - Post-quantum: **Dilithium (ML-DSA)**
2. **PQC-only authentication (later transition):** only PQ signatures once ecosystem support is mature.

Hybrid authentication is useful because it reduces the risk that a newly standardized PQ signature scheme has unforeseen weaknesses.

### Simple connection flow (sequence explanation)

Below is a conceptual hybrid handshake flow (protocol-agnostic).

1. Client → Server: Hello + supported algorithms
- Proposes:
    - ECDH curve(s): X25519, P-256, …
    - PQ KEM(s): ML-KEM-768, …
    - Symmetric cipher(s): AES-GCM, ChaCha20-Poly1305
    - Signature(s): ECDSA/RSA + Dilithium
1. Server → Client: ServerHello + server authentication
- Chooses algorithms
- Sends server certificate(s) / public keys
- Sends **classical signature** over handshake transcript
- Sends **PQC signature** (Dilithium) over handshake transcript (hybrid auth)
1. Key establishment (hybrid)
- **ECDH:** exchange ephemeral public keys, compute $s_{ecdh}$
- **ML-KEM:** server sends PQ public key (or has it in cert); client encapsulates → ciphertext; server decapsulates → $s_{pqc}$
1. Key schedule
- Both sides compute:
    - `master_secret = HKDF-Extract(salt, s_ecdh || s_pqc)`
    - Derive `client_write_key`, `server_write_key`, nonces/IVs, rekey keys
1. Secure tunnel starts
- Encrypted, authenticated traffic using derived symmetric keys
- Periodic **rekeying** (optional) using updated handshake or KDF chaining

Text-form diagram (high level):

- Client
    - generates ECDH ephemeral keypair
    - encapsulates to server ML-KEM public key → (ct, s_pqc)
    - computes s_ecdh
    - derives traffic keys via HKDF
- Server
    - generates ECDH ephemeral keypair
    - decapsulates ct with ML-KEM secret key → s_pqc
    - computes s_ecdh
    - derives same traffic keys via HKDF

---

## 4. Post-Quantum Cryptography (PQC) Overview

### What is PQC?

Post-Quantum Cryptography refers to cryptographic algorithms designed to remain secure against both:

- Classical computers, and
- Quantum computers (as far as we know today)

PQC primarily replaces the *public-key* parts of protocols:

- Key exchange / key encapsulation (e.g., ML-KEM)
- Digital signatures (e.g., ML-DSA / Dilithium)

Symmetric encryption (AES, ChaCha20) is believed to remain relatively safe, though Grover’s algorithm gives a square-root speedup; this is typically addressed by using appropriate key sizes (e.g., AES-256 when needed).

### Brief types of PQC

Common PQC families include:

- **Lattice-based:** strong efficiency and current standardization focus (e.g., Kyber/ML-KEM, Dilithium/ML-DSA)
- **Hash-based:** strong security foundations but often larger signatures or stateful designs (e.g., SPHINCS+)
- **Code-based:** long history, typically larger public keys (e.g., Classic McEliece)
- **Multivariate:** based on multivariate polynomial systems; some candidates had breaks historically

### Focus: Kyber (ML-KEM)

Kyber/ML-KEM is a lattice-based KEM designed for:

- Efficient key establishment
- Practical performance on common hardware
- Reasonable ciphertext/public key sizes compared to many alternatives

KEM interface (conceptual):

- `KeyGen()` → `(pk, sk)`
- `Encaps(pk)` → `(ct, ss)`
- `Decaps(sk, ct)` → `ss`

The shared secret `ss` becomes input to HKDF (along with other components).

### Focus: Dilithium (ML-DSA)

Dilithium/ML-DSA is a lattice-based digital signature scheme designed for:

- Efficient signing and verification
- Strong security in the post-quantum setting

Signature interface (conceptual):

- `KeyGen()` → `(pk, sk)`
- `Sign(sk, message)` → `sig`
- `Verify(pk, message, sig)` → `true/false`

In a VPN handshake, Dilithium can sign the handshake transcript (or a structured set of handshake messages) to authenticate the server (and optionally the client).

---

## 5. Implementation Guide (C++ + OpenSSL + liboqs)

This section describes a practical step-by-step path to build a hybrid cryptographic handshake suitable for a VPN-like secure channel. The same cryptographic building blocks can be integrated into WireGuard/OpenVPN/IPsec implementations or used to build a research prototype.

### Step 1: Choose a tech stack

Recommended (student-friendly, widely supported):

- **Language:** C++ (or C for lowest-level control)
- **Classical crypto:** OpenSSL (for ECDH, HKDF, AES-GCM)
- **Post-quantum crypto:** liboqs (Open Quantum Safe)

Notes:

- liboqs provides implementations of PQ KEMs and PQ signatures.
- There are OpenSSL integrations from Open Quantum Safe (OQS-OpenSSL), but for learning projects it can be simpler to call liboqs directly.

### Step 2: Define the handshake transcript

To prevent downgrade and transcript tampering, define a transcript hash:

- Append each handshake message in order.
- Maintain `transcript_hash = Hash(transcript_bytes)`.

Use SHA-256 or SHA-384 depending on your desired security level.

### Step 3: Perform classical key exchange (ECDH with OpenSSL)

Use an ephemeral ECDH exchange:

- Client generates ephemeral keypair
- Server generates ephemeral keypair
- Exchange public keys
- Compute shared secret `s_ecdh`

Pseudocode:

- Client:
    - `(c_priv, c_pub) = ECDH_Generate()`
    - send `c_pub`
- Server:
    - `(s_priv, s_pub) = ECDH_Generate()`
    - send `s_pub`
    - `s_ecdh = ECDH_Derive(s_priv, c_pub)`
- Client:
    - `s_ecdh = ECDH_Derive(c_priv, s_pub)`

### Step 4: Perform PQ key exchange (ML-KEM with liboqs)

Choose an ML-KEM parameter set (e.g., ML-KEM-768).

KEM pattern:

- Server:
    - `(pk_pqc, sk_pqc) = KEM_KeyGen()`
    - send `pk_pqc` (or embed in a certificate)
- Client:
    - `(ct, s_pqc) = KEM_Encaps(pk_pqc)`
    - send `ct`
- Server:
    - `s_pqc = KEM_Decaps(sk_pqc, ct)`

Important implementation notes:

- Treat `s_pqc` as secret key material.
- Validate algorithm identifiers and lengths.
- Use constant-time implementations (liboqs provides this for supported schemes).

### Step 5: Combine keys using HKDF

A straightforward hybrid key schedule:

- `ikm = s_ecdh || s_pqc`
- `prk = HKDF-Extract(salt = transcript_hash, IKM = ikm)`
- Derive traffic keys:
    - `client_key = HKDF-Expand(prk, info="client traffic", L=32)`
    - `server_key = HKDF-Expand(prk, info="server traffic", L=32)`
    - `client_iv  = HKDF-Expand(prk, info="client iv", L=12)`
    - `server_iv  = HKDF-Expand(prk, info="server iv", L=12)`

Why use `transcript_hash` as salt/info?

- Binds derived keys to the exact handshake messages.
- Makes downgrade attacks harder because negotiated parameters affect the transcript.

### Step 6: Encrypt communication (AES-GCM or ChaCha20-Poly1305)

Once keys are derived, encrypt data packets.

General requirements:

- Use a unique nonce/IV per key (never reuse).
- Include associated data (AAD) such as packet headers to protect them with integrity.

Pseudocode (AEAD send):

- `ciphertext, tag = AEAD_Encrypt(key, iv, plaintext, aad)`
- send `(iv, ciphertext, tag)`

Pseudocode (AEAD receive):

- `plaintext = AEAD_Decrypt(key, iv, ciphertext, aad, tag)`
- if verification fails → drop packet

### Step 7: Add authentication (classical + Dilithium)

For server authentication, sign the transcript:

- `sig_classical = Sign_ECDSA_or_RSA(server_classical_sk, transcript_hash)`
- `sig_pqc = Sign_Dilithium(server_dilithium_sk, transcript_hash)`

Client verifies both:

- Verify classical cert chain (PKI) and classical signature
- Verify Dilithium public key (distributed via cert extension, pinned key, or parallel trust channel) and PQ signature

Practical deployment options for hybrid auth:

- **Dual certificates:** one classical certificate + one PQ certificate
- **Single container:** classical certificate containing PQ public key as an extension (engineering effort)
- **Pinned PQ key:** distribute PQ public key out-of-band (simpler for prototypes)

### Minimal illustrative code skeleton (high-level)

This is intentionally simplified (error handling omitted) to show the flow.

1. Setup
- Load OpenSSL
- Choose curve (X25519/P-256)
- Choose PQ KEM (ML-KEM-768)
1. Handshake
- Exchange negotiation messages
- ECDH derive `s_ecdh`
- ML-KEM derive `s_pqc`
- `master = HKDF(transcript_hash, s_ecdh || s_pqc)`
- Derive AEAD keys
1. Data
- Use AEAD to encrypt/decrypt tunnel packets

Security checklist for a project:

- Include downgrade resistance (bind negotiated algorithms to transcript)
- Ensure nonce uniqueness
- Use constant-time primitives
- Handle key erasure (zeroize secrets after use)
- Add rekeying for long sessions

---

## 6. Real-World Applications

### Hybrid cryptography in TLS 1.3

Modern deployments increasingly use hybrid key exchange in TLS 1.3-like handshakes:

- Classical ECDHE provides security today
- PQ KEM provides protection against future quantum attacks
- Hybrid combination reduces migration risk

Some ecosystems have already experimented with hybrid TLS key exchanges (e.g., combining X25519 with Kyber-derived secrets) to prepare for standardization and operational rollout.

### Hybrid cryptography in modern VPNs

VPNs often reuse TLS (OpenVPN) or have their own handshake frameworks (WireGuard/Noise, IKEv2). Hybrid techniques can be integrated by:

- Adding PQ KEM ciphertexts/public keys to handshake messages
- Deriving session keys from both classical and PQ secrets

### Why companies are moving toward hybrid models

Drivers:

- Protect long-lived secrets against HNDL
- Meet regulatory and customer security expectations
- Avoid “flag day” migrations (hybrid allows gradual rollout)
- Maintain compatibility while PQ standards and tooling mature

---

## 7. Advantages and Challenges

### Advantages

- **Quantum resistance for key establishment:** protects confidentiality even if ECC becomes breakable by quantum computers.
- **Future-proofing:** reduces the risk that recorded traffic becomes decryptable later.
- **Risk balancing:** if a PQC scheme is weakened later, classical crypto may still provide protection (and vice versa).
- **Incremental migration:** hybrid modes can be deployed alongside existing infrastructure.

### Challenges

- **Performance overhead:** extra computations during handshake; may impact high-frequency reconnect scenarios.
- **Larger message sizes:** PQ public keys and ciphertexts are larger than ECC equivalents, increasing handshake bandwidth.
- **Compatibility and deployment complexity:**
    - negotiating new algorithms
    - updating clients/servers
    - handling middleboxes and legacy systems
- **Operational complexity:** key management, certificates, trust models for PQ public keys.
- **Cryptographic agility:** you must be able to swap algorithms as standards evolve.

---

## 8. Use Cases

### Government / military communications

- High-value targets with strong adversaries
- Long confidentiality lifetimes
- Need for secure communications even under future cryptanalytic advances

### Long-term sensitive data protection

- Medical records, legal records, R&D data
- Archives that must remain secret for 10–30+ years
- Protection against HNDL is especially important

### Enterprise VPNs

- Remote access VPNs for employees and contractors
- Site-to-site VPNs between offices and cloud environments
- Hybrid VPNs can provide a migration path while maintaining availability

---

## 9. Conclusion

Hybrid VPNs combine classical cryptography (like ECDH and ECDSA/RSA) with post-quantum algorithms (like Kyber/ML-KEM and Dilithium/ML-DSA) to protect secure tunnels against both present-day and future threats.

Key takeaways:

- Quantum computing threatens many currently deployed public-key systems (Shor’s algorithm).
- Attackers can store encrypted traffic today and decrypt later (“harvest now, decrypt later”).
- A hybrid handshake derives session keys from both classical and PQ secrets, improving resilience during the transition to quantum-safe security.

As organizations plan for the next decade of security, hybrid VPN designs offer a practical, incremental route toward quantum-safe systems without abandoning the proven strengths of classical cryptography.