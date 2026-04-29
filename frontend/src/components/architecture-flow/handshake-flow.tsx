"use client";

import {
  KeyRound,
  Lock,
  Send,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { FlowStep } from "./flow-step";

/* ── Reusable detail block ───────────────────────────────────────────── */

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2 text-sm">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="truncate font-mono text-xs text-foreground/80">{value}</span>
    </div>
  );
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre className="mt-3 overflow-x-auto rounded-xl border border-border/60 bg-muted/30 p-4 text-xs leading-relaxed text-foreground/80 font-mono">
      {children}
    </pre>
  );
}

/* ── Section ─────────────────────────────────────────────────────────── */

export function HandshakeFlow(): React.JSX.Element {
  return (
    <div>
      {/* Step 1 — Authentication */}
      <FlowStep
        stepNumber={1}
        title="Gateway Authentication"
        subtitle="Client proves identity via Argon2id-verified credentials."
        icon={UserCheck}
        accentClass="bg-amber-500/10 text-amber-400 ring-amber-500/20"
      >
        <div className="space-y-2">
          <DetailRow label="Endpoint" value="POST /auth" />
          <DetailRow label="Hashing" value="Argon2id (password hasher)" />
          <DetailRow label="Users" value="Configured per-gateway (demo: demo / demo-vpn-2026)" />
        </div>
        <CodeBlock>{`Agent → Gateway:  { username, password }
Gateway:          argon2id.verify(stored_hash, password)
Gateway → Agent:  { authenticated: true }`}</CodeBlock>
      </FlowStep>

      {/* Step 2 — ClientHello */}
      <FlowStep
        stepNumber={2}
        title="Client Hello"
        subtitle="Agent generates ephemeral key pairs and sends public halves."
        icon={Send}
        accentClass="bg-sky-500/10 text-sky-400 ring-sky-500/20"
      >
        <div className="space-y-2">
          <DetailRow label="X25519" value="32-byte ephemeral public key" />
          <DetailRow label="ML-KEM-768" value="1,184-byte public key (if liboqs available)" />
          <DetailRow label="Suite" value="X25519MLKEM768_AES256GCM_ECDSA_P256" />
        </div>
        <CodeBlock>{`x25519_priv  = X25519PrivateKey.generate()
x25519_pub   = x25519_priv.public_key()       →  32 bytes

mlkem_kp     = kem_keygen("ML-KEM-768")
mlkem_pub    = mlkem_kp.public_key             →  1,184 bytes

ClientHello  = { suite, x25519_pub, mlkem_pub }`}</CodeBlock>
      </FlowStep>

      {/* Step 3 — ServerHello */}
      <FlowStep
        stepNumber={3}
        title="Server Hello"
        subtitle="Gateway derives shared secrets, encapsulates ML-KEM, and signs the transcript."
        icon={ShieldCheck}
        accentClass="bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
      >
        <div className="space-y-2">
          <DetailRow label="ECDH" value="X25519 DH → 32-byte shared secret" />
          <DetailRow label="KEM" value="ML-KEM-768 encapsulate → ciphertext + shared secret" />
          <DetailRow label="Transcript" value="SHA-256 over [suite, client_pub, server_pub, mlkem_pub, ct]" />
          <DetailRow label="Signature" value="ECDSA-P256 over transcript digest" />
        </div>
        <CodeBlock>{`server_priv  = X25519PrivateKey.generate()
ecdh_ss      = server_priv.exchange(client_x25519_pub)   →  32 bytes

(ct, pqc_ss) = kem_encapsulate(client_mlkem_pub)
               ct  →  1,088 bytes   pqc_ss  →  32 bytes

digest       = SHA-256( len‖suite ‖ len‖client_pub ‖ len‖server_pub
                      ‖ len‖mlkem_pub ‖ len‖ct )
signature    = ECDSA_P256.sign(identity_key, digest)

ServerHello  = { server_pub, ct, signature, ecdsa_pub_der, digest }`}</CodeBlock>
      </FlowStep>

      {/* Step 4 — Key Schedule */}
      <FlowStep
        stepNumber={4}
        title="Hybrid Key Schedule"
        subtitle="Both sides derive identical traffic secrets from combined key material."
        icon={KeyRound}
        accentClass="bg-violet-500/10 text-violet-400 ring-violet-500/20"
      >
        <div className="space-y-2">
          <DetailRow label="Combination" value="pqc_shared_secret ‖ ecdh_shared_secret" />
          <DetailRow label="KDF" value="HKDF-SHA256 with transcript digest as salt" />
          <DetailRow label="Output" value="4 keys — client_key, server_key, client_nonce, server_nonce" />
        </div>
        <CodeBlock>{`combined  = pqc_ss ‖ ecdh_ss          →  64 bytes

client_key        = HKDF(info="rvce client traffic",  key=combined, salt=digest, len=32)
server_key        = HKDF(info="rvce server traffic",  key=combined, salt=digest, len=32)
client_nonce_base = HKDF(info="rvce client nonce",    key=combined, salt=digest, len=12)
server_nonce_base = HKDF(info="rvce server nonce",    key=combined, salt=digest, len=12)

Client verifies: ECDSA_P256.verify(server_pub_key, digest, signature)  ✓`}</CodeBlock>
      </FlowStep>

      {/* Step 5 — Session start */}
      <FlowStep
        stepNumber={5}
        title="Gateway Session"
        subtitle="Gateway starts its TUN device, NAT, and forwarding before the agent opens its side."
        icon={Lock}
        accentClass="bg-rose-500/10 text-rose-400 ring-rose-500/20"
        isLast
      >
        <div className="space-y-2">
          <DetailRow label="Endpoint" value="POST /session/start" />
          <DetailRow label="Gateway TUN" value="hyb-gw0 at 10.42.0.1/24" />
          <DetailRow label="Client TUN" value="hyb0 at 10.42.0.2/24" />
          <DetailRow label="NAT" value="iptables MASQUERADE on uplink interface" />
        </div>
        <CodeBlock>{`Gateway:
  TUN hyb-gw0  → open /dev/net/tun → ip addr 10.42.0.1/24 → UP
  iptables -A FORWARD -i hyb-gw0 -o eth0 -j ACCEPT
  iptables -t nat -A POSTROUTING -s 10.42.0.0/24 -o eth0 -j MASQUERADE
  UDP bind :4433 → ready for encrypted datagrams

Agent:
  TUN hyb0     → open /dev/net/tun → ip addr 10.42.0.2/24 → UP
  UDP bind :4434 → target gateway:4433
  ip route replace default dev hyb0   (full-tunnel override)`}</CodeBlock>
      </FlowStep>
    </div>
  );
}
