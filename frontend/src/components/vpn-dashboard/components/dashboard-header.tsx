import { Shield } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

type DashboardHeaderProps = {
  isOnline: boolean;
};

export function DashboardHeader({ isOnline }: DashboardHeaderProps): React.JSX.Element {
  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Shield className="size-[18px]" />
        </div>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Hybrid PQC VPN
          </h1>
          <span className="flex items-center gap-1.5 rounded-full border border-border/60 bg-muted/50 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
            <span
              className={`block size-1.5 rounded-full ${
                isOnline
                  ? "bg-emerald-500 animate-pulse-dot"
                  : "bg-muted-foreground/40"
              }`}
            />
            {isOnline ? "Online" : "Offline"}
          </span>
        </div>
      </div>
      <ThemeToggle />
    </header>
  );
}
