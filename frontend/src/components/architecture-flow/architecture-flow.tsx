"use client";

import { FlowHero } from "./flow-hero";
import { HandshakeFlow } from "./handshake-flow";
import { TunnelFlow } from "./tunnel-flow";
import { CryptoDetail } from "./crypto-detail";
import { Separator } from "@/components/ui/separator";

export function ArchitectureFlow(): React.JSX.Element {
  return (
    <div className="min-h-screen bg-background">
      <FlowHero />
      
      <div className="mx-auto max-w-4xl px-4 pb-24 sm:px-6">
        <div className="space-y-16">
          <section>
            <div className="mb-10">
              <p className="text-xs font-medium uppercase tracking-[0.25em] text-primary">
                Control Plane
              </p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                The Hybrid Handshake
              </h2>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                A single-round protocol designed for high-latency VM environments,
                combining classical and post-quantum security.
              </p>
            </div>
            <HandshakeFlow />
          </section>

          <Separator className="opacity-40" />

          <section>
            <TunnelFlow />
          </section>

          <Separator className="opacity-40" />

          <section>
            <CryptoDetail />
          </section>
        </div>
      </div>
    </div>
  );
}
