"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

/* ── Algorithm card ──────────────────────────────────────────────────── */

type AlgorithmProps = {
  name: string;
  purpose: string;
  spec: string;
  keySize: string;
  colorClass: string;
  delay: number;
};

function AlgorithmBlock({
  name,
  purpose,
  spec,
  keySize,
  colorClass,
  delay,
}: AlgorithmProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, delay }}
      className="relative overflow-hidden rounded-xl border border-border/40 bg-muted/10 p-5"
    >
      {/* Accent stripe */}
      <div className={`absolute left-0 top-0 h-full w-1 ${colorClass}`} />

      <div className="pl-3">
        <h4 className="text-sm font-semibold text-foreground">{name}</h4>
        <p className="mt-0.5 text-xs text-muted-foreground">{purpose}</p>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <span className="text-muted-foreground">
            Spec: <span className="font-mono text-foreground/70">{spec}</span>
          </span>
          <span className="text-muted-foreground">
            Key: <span className="font-mono text-foreground/70">{keySize}</span>
          </span>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Section ─────────────────────────────────────────────────────────── */

export function CryptoDetail(): React.JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section ref={ref} className="mt-4 mb-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
      >
        <p className="text-xs font-medium uppercase tracking-[0.25em] text-primary">
          Cryptographic Primitives
        </p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Algorithm Suite
        </h2>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">
          Four algorithms form a defence-in-depth stack. The hybrid key exchange
          ensures security even if one primitive is compromised.
        </p>
      </motion.div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <AlgorithmBlock
          name="X25519 (ECDH)"
          purpose="Classical key exchange — provides forward secrecy"
          spec="RFC 7748 / Curve25519"
          keySize="32 bytes"
          colorClass="bg-sky-400"
          delay={0.1}
        />
        <AlgorithmBlock
          name="ML-KEM-768"
          purpose="Post-quantum key encapsulation — quantum-resistant key agreement"
          spec="NIST FIPS 203 (Kyber)"
          keySize="PK 1,184 B · CT 1,088 B · SS 32 B"
          colorClass="bg-violet-400"
          delay={0.2}
        />
        <AlgorithmBlock
          name="AES-256-GCM"
          purpose="Authenticated encryption — protects tunnel data with integrity"
          spec="NIST SP 800-38D"
          keySize="256-bit key · 96-bit nonce"
          colorClass="bg-primary"
          delay={0.3}
        />
        <AlgorithmBlock
          name="ECDSA P-256"
          purpose="Transcript authentication — server identity & handshake integrity"
          spec="NIST FIPS 186-5 / secp256r1"
          keySize="256-bit (sign + verify)"
          colorClass="bg-amber-400"
          delay={0.4}
        />
      </div>

      {/* Hybrid explanation */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="mt-6 rounded-xl border border-primary/20 bg-primary/5 p-5"
      >
        <h4 className="text-sm font-semibold text-primary">Why Hybrid?</h4>
        <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
          The PQC shared secret (ML-KEM) is concatenated <em>before</em> the
          classical shared secret (X25519), then fed through HKDF-SHA256. If a
          quantum computer breaks X25519, the ML-KEM layer still protects the
          session. If ML-KEM has an undiscovered vulnerability, the classical
          X25519 layer remains secure. Both must be compromised simultaneously.
        </p>
      </motion.div>
    </section>
  );
}
