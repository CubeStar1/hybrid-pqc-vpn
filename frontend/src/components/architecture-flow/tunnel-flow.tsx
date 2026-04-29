"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight, Lock, Unlock } from "lucide-react";

/* ── Animated packet dot ─────────────────────────────────────────────── */

function PacketDot({
  delay,
  color = "bg-primary",
}: {
  delay: number;
  color?: string;
}) {
  return (
    <motion.div
      className={`absolute top-1/2 size-2 -translate-y-1/2 rounded-full ${color} shadow-[0_0_8px_2px] shadow-primary/40`}
      initial={{ left: "0%", opacity: 0 }}
      animate={{
        left: ["0%", "100%"],
        opacity: [0, 1, 1, 0],
      }}
      transition={{
        duration: 2.4,
        delay,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}

/* ── Tunnel pipe visual ──────────────────────────────────────────────── */

function TunnelPipe({
  label,
  direction,
  packets,
}: {
  label: string;
  direction: "right" | "left";
  packets: number;
}) {
  return (
    <div className="flex items-center gap-3">
      {direction === "right" && (
        <span className="shrink-0 text-xs font-medium text-muted-foreground w-16 text-right">{label}</span>
      )}
      <div className="relative h-6 flex-1 overflow-hidden rounded-full border border-border/40 bg-muted/20">
        {Array.from({ length: packets }).map((_, i) => (
          <PacketDot
            key={i}
            delay={i * 0.6}
            color={direction === "right" ? "bg-primary" : "bg-emerald-400"}
          />
        ))}
      </div>
      {direction === "left" && (
        <span className="shrink-0 text-xs font-medium text-muted-foreground w-16">{label}</span>
      )}
    </div>
  );
}

/* ── Main section ────────────────────────────────────────────────────── */

export function TunnelFlow(): React.JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section ref={ref} className="mt-4 mb-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 }}
        transition={{ duration: 0.5 }}
      >
        {/* Section header */}
        <div className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.25em] text-primary">
            Data Plane
          </p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Encrypted Tunnel Transport
          </h2>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">
            IP packets flow through the TUN interface, get encrypted with
            AES-256-GCM, and travel over UDP datagrams with sequence-number
            replay protection.
          </p>
        </div>

        {/* Tunnel diagram */}
        <div className="rounded-2xl border border-border/60 bg-muted/10 p-6 sm:p-8">
          {/* Endpoints row */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 sm:gap-6">
            {/* Client */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="text-center"
            >
              <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-sky-500/10 text-sky-400 ring-1 ring-sky-500/20 sm:size-16">
                <Unlock className="size-6" />
              </div>
              <p className="mt-2 text-sm font-semibold text-foreground">Agent</p>
              <p className="text-xs text-muted-foreground">TUN hyb0</p>
              <p className="font-mono text-[11px] text-muted-foreground/70">10.42.0.2</p>
            </motion.div>

            {/* Arrow */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={isInView ? { opacity: 1, scale: 1 } : {}}
              transition={{ delay: 0.35, duration: 0.3 }}
              className="flex flex-col items-center gap-1"
            >
              <ArrowRight className="size-5 text-muted-foreground" />
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                UDP :4433
              </span>
            </motion.div>

            {/* Gateway */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="text-center"
            >
              <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20 sm:size-16">
                <Lock className="size-6" />
              </div>
              <p className="mt-2 text-sm font-semibold text-foreground">Gateway</p>
              <p className="text-xs text-muted-foreground">TUN hyb-gw0</p>
              <p className="font-mono text-[11px] text-muted-foreground/70">10.42.0.1</p>
            </motion.div>
          </div>

          {/* Animated packet pipes */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="mt-8 space-y-3"
          >
            <TunnelPipe label="Outbound" direction="right" packets={3} />
            <TunnelPipe label="Inbound" direction="left" packets={3} />
          </motion.div>

          {/* Packet frame detail */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.65, duration: 0.4 }}
            className="mt-6 rounded-xl border border-border/40 bg-background/60 p-4"
          >
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              UDP Datagram Frame
            </p>
            <div className="flex items-stretch gap-0.5 text-center text-[11px] font-mono">
              <div className="flex-[1] rounded-l-lg bg-violet-500/15 py-2.5 text-violet-400 ring-1 ring-violet-500/20">
                SEQ<br />
                <span className="text-[10px] text-violet-400/60">4 B</span>
              </div>
              <div className="flex-[6] bg-primary/10 py-2.5 text-primary ring-1 ring-primary/15">
                AES-256-GCM Encrypted Payload<br />
                <span className="text-[10px] text-primary/60">variable</span>
              </div>
              <div className="flex-[2] rounded-r-lg bg-amber-500/10 py-2.5 text-amber-400 ring-1 ring-amber-500/15">
                GCM Tag<br />
                <span className="text-[10px] text-amber-400/60">16 B</span>
              </div>
            </div>
            <div className="mt-3 space-y-1 text-xs text-muted-foreground">
              <p>• 12-byte nonce = <code className="rounded bg-muted/50 px-1 py-0.5 text-foreground/70">seq(4B) ‖ 0x00(8B)</code></p>
              <p>• Replay protection: reject packets with seq ≤ last received window</p>
              <p>• Max packet size: 2,048 bytes · TUN MTU: 1,280 bytes</p>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}
