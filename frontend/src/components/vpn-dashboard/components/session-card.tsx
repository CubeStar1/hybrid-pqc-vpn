import { Cpu, LaptopMinimal, Network, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";

type SessionInfo = {
  profileId: string;
  username: string;
  suite: string;
  state: string;
  tunnelActive: boolean;
  remoteEndpoint?: string | null;
  localAddress?: string | null;
  transcriptHash?: string | null;
  pqcEnabled: boolean;
};

type SessionCardProps = {
  session?: SessionInfo | null;
};

export function SessionCard({ session }: SessionCardProps): React.JSX.Element {
  if (!session) {
    return (
      <div className="bento-card flex items-center justify-center p-8 animate-tile-in" style={{ animationDelay: "120ms" }}>
        <p className="text-sm text-muted-foreground text-center">
          No active session.{" "}
          <span className="text-muted-foreground/60">Connect to view tunnel details.</span>
        </p>
      </div>
    );
  }

  return (
    <div className="bento-card p-5 space-y-4 animate-tile-in" style={{ animationDelay: "120ms" }}>
      {/* Header row */}
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground/70">
            Tunnel status
          </p>
          <p className="text-lg font-semibold capitalize text-foreground leading-tight mt-0.5">
            {session.tunnelActive ? "Active" : "Handshake Complete"}
          </p>
        </div>
        <Badge variant="outline" className="rounded-full text-[10px] font-mono shrink-0 max-w-[180px] truncate">
          {session.suite}
        </Badge>
      </div>

      {/* Detail rows */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-3">
        <SessionRow icon={Network} label="Profile" value={session.profileId} />
        <SessionRow icon={LaptopMinimal} label="Username" value={session.username} />
        <SessionRow icon={Cpu} label="PQC" value={session.pqcEnabled ? "Enabled" : "Disabled"} />
        <SessionRow
          icon={ShieldAlert}
          label="Transcript"
          value={session.transcriptHash?.slice(0, 16) ?? "Pending"}
        />
        <SessionRow
          icon={Network}
          label="Tunnel endpoint"
          value={session.remoteEndpoint ?? (session.tunnelActive ? "Active" : "Unavailable")}
        />
        <SessionRow
          icon={LaptopMinimal}
          label="Local address"
          value={session.localAddress ?? (session.tunnelActive ? "Assigned" : "Unavailable")}
        />
      </div>
    </div>
  );
}

function SessionRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Network;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-1.5 mb-0.5">
        <Icon className="size-3 text-muted-foreground/60 shrink-0" />
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground/70">{label}</span>
      </div>
      <p className="text-sm font-medium text-foreground truncate">{value}</p>
    </div>
  );
}
