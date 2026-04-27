import { Loader2, PlugZap, RefreshCw, ShieldCheck, ShieldOff } from "lucide-react";

import { Button } from "@/components/ui/button";

type ConnectionPanelProps = {
  isConnected: boolean;
  sessionState: string;
  profileName: string;
  connectMessage: string;
  lastHandshake: string;
  canConnect: boolean;
  isBusy: boolean;
  isRefreshing: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onRefresh: () => void;
};

export function ConnectionPanel({
  isConnected,
  sessionState,
  profileName,
  connectMessage,
  lastHandshake,
  canConnect,
  isBusy,
  isRefreshing,
  onConnect,
  onDisconnect,
  onRefresh,
}: ConnectionPanelProps): React.JSX.Element {
  return (
    <section className="space-y-5">
      <h2 className="text-lg font-semibold text-foreground">Connection</h2>

      {/* Primary workspace — state is the dominant idea, actions below */}
      <div className="rounded-2xl border border-border/60 bg-gradient-to-br from-primary/8 via-transparent to-transparent p-5 space-y-5">
        {/* Status display */}
        <div className="flex items-center gap-4">
          <div
            className={`flex size-11 shrink-0 items-center justify-center rounded-full transition-colors ${
              isConnected
                ? "bg-emerald-500 text-white"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {isConnected ? (
              <ShieldCheck className="size-5" />
            ) : (
              <ShieldOff className="size-5" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-2xl font-semibold capitalize text-foreground leading-tight">
              {sessionState}
            </p>
            <p className="text-sm text-muted-foreground truncate">{profileName}</p>
          </div>
        </div>

        {/* Actions — single row, left-aligned, uniform sizing */}
        <div className="flex items-center gap-2.5">
          <Button
            className="rounded-full px-5"
            onClick={onConnect}
            disabled={!canConnect || isBusy}
          >
            {isBusy ? <Loader2 className="size-4 animate-spin" /> : <PlugZap className="size-4" />}
            {isConnected ? "Reconnect" : "Connect"}
          </Button>
          <Button
            variant="outline"
            className="rounded-full px-5"
            onClick={onDisconnect}
            disabled={!isConnected || isBusy}
          >
            <ShieldOff className="size-4" />
            Disconnect
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full ml-auto"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
            <span className="sr-only">Refresh</span>
          </Button>
        </div>
      </div>

      {/* Status rows */}
      <div className="grid gap-px overflow-hidden rounded-xl border border-border/60 bg-border/40 sm:grid-cols-2">
        <div className="bg-background px-4 py-3">
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
            Agent response
          </p>
          <p className="mt-1.5 text-sm text-foreground">{connectMessage}</p>
        </div>
        <div className="bg-background px-4 py-3">
          <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
            Handshake
          </p>
          <p className="mt-1.5 text-sm text-foreground">{lastHandshake}</p>
        </div>
      </div>
    </section>
  );
}
