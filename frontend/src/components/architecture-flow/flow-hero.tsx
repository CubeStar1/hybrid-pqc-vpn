"use client";

import { motion } from "framer-motion";
import { Shield } from "lucide-react";

export function FlowHero(): React.JSX.Element {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24">
      {/* Subtle grid background */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03]">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mx-auto mb-6 flex size-16 items-center justify-center rounded-2xl bg-primary/10 text-primary ring-1 ring-primary/20"
        >
          <Shield className="size-7" />
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="text-xs font-medium uppercase tracking-[0.3em] text-primary"
        >
          Hybrid PQC VPN · Architecture
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.5 }}
          className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl"
        >
          Connection &amp; Encryption Flow
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base"
        >
          From authentication through hybrid post-quantum handshake to encrypted
          tunnel transport — every stage of the VPN lifecycle, visualised.
        </motion.p>

        {/* Suite badge */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.4 }}
          className="mt-6 inline-flex items-center gap-2 rounded-full border border-border/60 bg-muted/40 px-4 py-1.5 text-xs font-mono text-muted-foreground"
        >
          <span className="size-1.5 rounded-full bg-primary animate-pulse-dot" />
          X25519 · ML-KEM-768 · AES-256-GCM · ECDSA-P256
        </motion.div>
      </div>
    </section>
  );
}
