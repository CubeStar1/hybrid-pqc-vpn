import { Activity, Binary, Fingerprint, ShieldCheck } from "lucide-react";

type NetworkOverviewProps = {
  isOnline: boolean;
  oqsAvailable: boolean;
  identityReady: boolean;
  transcriptBytes?: number;
};

type IndicatorProps = {
  icon: typeof Activity;
  label: string;
  value: string;
  ok: boolean;
};

function Indicator({ icon: Icon, label, value, ok }: IndicatorProps) {
  return (
    <div className="flex items-center gap-2.5 py-2">
      <Icon className="size-3.5 text-muted-foreground/70 shrink-0" />
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={`ml-auto text-xs font-medium ${
          ok
            ? "text-emerald-600 dark:text-emerald-400"
            : "text-muted-foreground"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

export function NetworkOverview({
  isOnline,
  oqsAvailable,
  identityReady,
  transcriptBytes,
}: NetworkOverviewProps): React.JSX.Element {
  return (
    <section className="flex flex-wrap items-center gap-x-6 gap-y-1 border-y border-border/60 px-1 py-1 md:divide-x md:divide-border/50 md:gap-0">
      <div className="flex-1 min-w-[140px] px-3">
        <Indicator icon={Activity} label="Agent" value={isOnline ? "Online" : "Offline"} ok={isOnline} />
      </div>
      <div className="flex-1 min-w-[140px] px-3">
        <Indicator icon={Binary} label="PQC" value={oqsAvailable ? "Ready" : "Unavailable"} ok={oqsAvailable} />
      </div>
      <div className="flex-1 min-w-[140px] px-3">
        <Indicator icon={Fingerprint} label="Identity" value={identityReady ? "Pinned" : "Pending"} ok={identityReady} />
      </div>
      <div className="flex-1 min-w-[140px] px-3">
        <Indicator
          icon={ShieldCheck}
          label="Handshake"
          value={transcriptBytes ? `${transcriptBytes} B` : "—"}
          ok={Boolean(transcriptBytes)}
        />
      </div>
    </section>
  );
}
