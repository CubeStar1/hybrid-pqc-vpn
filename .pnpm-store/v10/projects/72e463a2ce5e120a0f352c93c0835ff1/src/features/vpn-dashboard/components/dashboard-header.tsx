import { Globe2, Shield } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";

export function DashboardHeader(): React.JSX.Element {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-3">
        <Badge
          variant="outline"
          className="w-fit rounded-full border-primary/20 bg-primary/5 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-primary"
        >
          Secure VPN
        </Badge>
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <Shield className="size-5" />
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                VPN Dashboard
              </h1>
              <p className="text-sm text-muted-foreground">
                Connect quickly, monitor tunnel health, and switch servers without the clutter.
              </p>
            </div>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/70 px-3 py-1 text-xs text-muted-foreground">
            <Globe2 className="size-3.5 text-primary" />
            Optimized for a simple client-style control surface
          </div>
        </div>
      </div>
      <ThemeToggle />
    </header>
  );
}
