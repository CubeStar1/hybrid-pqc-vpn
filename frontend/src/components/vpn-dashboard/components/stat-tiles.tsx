import { Activity, Binary, Fingerprint, ShieldCheck } from "lucide-react";

type StatTilesProps = {
  isOnline: boolean;
  oqsAvailable: boolean;
  identityReady: boolean;
  transcriptBytes?: number;
};

type TileProps = {
  icon: typeof Activity;
  label: string;
  value: string;
  ok: boolean;
  delay: string;
};

function Tile({ icon: Icon, label, value, ok, delay }: TileProps) {
  return (
    <div
      className="bento-card flex h-full min-h-0 flex-col items-center justify-center gap-2 p-4 text-center animate-tile-in"
      style={{ animationDelay: delay }}
    >
      <div
        className={`flex size-10 items-center justify-center rounded-xl transition-colors ${
          ok
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-muted/50 text-muted-foreground"
        }`}
      >
        <Icon className="size-4.5" />
      </div>
      <span className="text-lg font-semibold text-foreground">{value}</span>
      <span className="text-[11px] tracking-wide text-muted-foreground uppercase">{label}</span>
    </div>
  );
}

export function StatTiles({
  isOnline,
  oqsAvailable,
  identityReady,
  transcriptBytes,
}: StatTilesProps): React.JSX.Element {
  return (
    <div className="grid h-full grid-cols-2 grid-rows-2 gap-3">
      <Tile
        icon={Activity}
        label="Agent"
        value={isOnline ? "Online" : "Offline"}
        ok={isOnline}
        delay="0ms"
      />
      <Tile
        icon={Binary}
        label="PQC"
        value={oqsAvailable ? "Ready" : "N/A"}
        ok={oqsAvailable}
        delay="60ms"
      />
      <Tile
        icon={Fingerprint}
        label="Identity"
        value={identityReady ? "Pinned" : "Pending"}
        ok={identityReady}
        delay="120ms"
      />
      <Tile
        icon={ShieldCheck}
        label="Handshake"
        value={transcriptBytes ? `${transcriptBytes} B` : "—"}
        ok={Boolean(transcriptBytes)}
        delay="180ms"
      />
    </div>
  );
}
