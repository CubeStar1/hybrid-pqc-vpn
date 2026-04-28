import { Loader2, Power, PlugZap, RefreshCw, ShieldCheck, ShieldOff } from "lucide-react";

import { Button } from "@/components/ui/button";

type ConnectionHeroProps = {
  isConnected: boolean;
  isTunnelActive: boolean;
  sessionState: string;
  profileName: string;
  canConnect: boolean;
  isBusy: boolean;
  isRefreshing: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onRefresh: () => void;
};

export function ConnectionHero({
  isConnected,
  isTunnelActive,
  sessionState,
  profileName,
  canConnect,
  isBusy,
  isRefreshing,
  onConnect,
  onDisconnect,
  onRefresh,
}: ConnectionHeroProps): React.JSX.Element {
  const statusTitle = isConnected
    ? isTunnelActive
      ? "Tunnel Active"
      : "Session Ready"
    : sessionState === "checking"
      ? "Connecting…"
      : "Disconnected";

  const statusSubtitle = isConnected && !isTunnelActive
    ? `${profileName} · needs TUN permissions`
    : profileName;

  return (
    <div className="bento-card bento-card-hero col-span-full lg:col-span-1 flex flex-col items-center justify-center gap-6 p-8 relative overflow-hidden">
      {/* Background shimmer */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/3 pointer-events-none" />

      {/* Status icon */}
      <div className="relative">
        <div
          className={`flex size-20 items-center justify-center rounded-full transition-all duration-500 ${
            isConnected
              ? isTunnelActive
                ? "bg-emerald-500/15 text-emerald-400 ring-2 ring-emerald-500/20"
                : "bg-amber-500/15 text-amber-400 ring-2 ring-amber-500/20"
              : "bg-muted/50 text-muted-foreground ring-2 ring-border/40"
          }`}
        >
          {isConnected ? (
            <ShieldCheck className="size-9" />
          ) : (
            <ShieldOff className="size-9" />
          )}
        </div>
        {isConnected && (
          <span className="absolute -bottom-1 -right-1 flex size-5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex rounded-full size-5 bg-emerald-500" />
          </span>
        )}
      </div>

      {/* Status text */}
      <div className="text-center relative z-10">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">
          {statusTitle}
        </h2>
        <p className="mt-1.5 text-sm text-muted-foreground">{statusSubtitle}</p>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-3 relative z-10">
        {isConnected ? (
          <Button
            variant="outline"
            size="lg"
            className="rounded-full px-8 gap-2 border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={onDisconnect}
            disabled={isBusy}
          >
            {isBusy ? <Loader2 className="size-4 animate-spin" /> : <Power className="size-4" />}
            Disconnect
          </Button>
        ) : (
          <Button
            size="lg"
            className="rounded-full px-8 gap-2"
            onClick={onConnect}
            disabled={!canConnect || isBusy}
          >
            {isBusy ? <Loader2 className="size-4 animate-spin" /> : <PlugZap className="size-4" />}
            Connect
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="rounded-full size-10"
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
          <span className="sr-only">Refresh</span>
        </Button>
      </div>
    </div>
  );
}
