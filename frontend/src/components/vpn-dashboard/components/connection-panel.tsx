import { Loader2, PlugZap, RefreshCw, ShieldCheck, ShieldOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
    <Card className="border-border/70 bg-card/90 shadow-lg shadow-black/5">
      <CardHeader className="border-b border-border/60">
        <CardTitle className="text-xl">Connection</CardTitle>
        <CardDescription>
          One place to connect, disconnect, and check whether the tunnel is healthy.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        <div className="rounded-[2rem] border border-border/70 bg-gradient-to-br from-primary/12 via-background to-background p-6">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Current state</p>
              <div className="flex items-center gap-3">
                <div
                  className={`flex size-12 items-center justify-center rounded-full ${
                    isConnected ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isConnected ? <ShieldCheck className="size-5" /> : <ShieldOff className="size-5" />}
                </div>
                <div>
                  <p className="text-3xl font-semibold capitalize text-foreground">{sessionState}</p>
                  <p className="text-sm text-muted-foreground">{profileName}</p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button size="lg" className="rounded-full px-6" onClick={onConnect} disabled={!canConnect || isBusy}>
                {isBusy ? <Loader2 className="animate-spin" /> : <PlugZap />}
                {isConnected ? "Reconnect" : "Connect"}
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="rounded-full px-6"
                onClick={onDisconnect}
                disabled={!isConnected || isBusy}
              >
                <ShieldOff />
                Disconnect
              </Button>
              <Button
                size="lg"
                variant="ghost"
                className="rounded-full px-5"
                onClick={onRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={isRefreshing ? "animate-spin" : ""} />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-3 rounded-3xl border border-border/60 bg-muted/30 p-4 sm:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Agent response</p>
            <p className="mt-2 text-sm leading-6 text-foreground">{connectMessage}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Handshake</p>
            <p className="mt-2 text-sm leading-6 text-foreground">{lastHandshake}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
