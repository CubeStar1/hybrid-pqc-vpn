import { Cpu, LaptopMinimal, Network, Server, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type SessionInfo = {
  profileId: string;
  username: string;
  suite: string;
  state: string;
  transcriptHash?: string | null;
  pqcEnabled: boolean;
  notes: string[];
};

type RuntimeInfo = {
  defaultAgentApi?: string;
  defaultGatewayApi?: string;
  electronVersion?: string;
  nodeVersion?: string;
  platform?: string;
  notes?: string[];
};

type ActivityPanelProps = {
  session?: SessionInfo | null;
  runtime?: RuntimeInfo;
};

export function ActivityPanel({ session, runtime }: ActivityPanelProps): React.JSX.Element {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-foreground">Details</h2>

      <Tabs defaultValue="session">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="session">Session</TabsTrigger>
          <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
        </TabsList>

        <TabsContent value="session" className="mt-4 space-y-4">
          {session ? (
            <>
              <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/20 px-4 py-3">
                <div>
                  <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
                    Active tunnel
                  </p>
                  <p className="mt-1 text-lg font-semibold capitalize text-foreground">
                    {session.state}
                  </p>
                </div>
                <Badge variant="outline" className="rounded-full">
                  {session.suite}
                </Badge>
              </div>

              <dl className="grid gap-x-6 gap-y-0 rounded-xl border border-border/60 overflow-hidden bg-border/40 sm:grid-cols-2">
                <DetailRow icon={Network} label="Profile" value={session.profileId} />
                <DetailRow icon={LaptopMinimal} label="Username" value={session.username} />
                <DetailRow icon={Cpu} label="PQC" value={session.pqcEnabled ? "Enabled" : "Disabled"} />
                <DetailRow
                  icon={ShieldAlert}
                  label="Transcript"
                  value={session.transcriptHash?.slice(0, 16) ?? "Pending"}
                />
              </dl>

              {session.notes.length > 0 && (
                <div className="space-y-1.5 rounded-xl border border-border/60 bg-background px-4 py-3">
                  <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
                    Notes
                  </p>
                  {session.notes.map((note) => (
                    <p key={note} className="text-sm text-foreground">
                      {note}
                    </p>
                  ))}
                </div>
              )}
            </>
          ) : (
            <EmptyState text="No active session. Connect to see tunnel details." />
          )}
        </TabsContent>

        <TabsContent value="diagnostics" className="mt-4 space-y-4">
          <dl className="grid gap-px rounded-xl border border-border/60 overflow-hidden bg-border/40 sm:grid-cols-2">
            <DetailRow icon={Server} label="Agent API" value={runtime?.defaultAgentApi ?? "—"} />
            <DetailRow icon={Network} label="Gateway API" value={runtime?.defaultGatewayApi ?? "—"} />
            <DetailRow icon={LaptopMinimal} label="Electron" value={runtime?.electronVersion ?? "Browser"} />
            <DetailRow icon={Cpu} label="Node" value={runtime?.nodeVersion ?? "—"} />
          </dl>
          <Separator />
          <div className="space-y-1.5 rounded-xl border border-border/60 bg-background px-4 py-3">
            <p className="text-[11px] uppercase tracking-widest text-muted-foreground">
              Platform
            </p>
            <p className="text-sm font-medium text-foreground">
              {runtime?.platform ?? "web"}
            </p>
            {(runtime?.notes ?? []).map((note) => (
              <p key={note} className="text-sm text-muted-foreground">
                {note}
              </p>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </section>
  );
}

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Server;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 bg-background px-4 py-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="size-3.5 text-primary shrink-0" />
        {label}
      </div>
      <p className="break-all text-sm font-medium text-foreground text-right">{value}</p>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border/60 bg-muted/10 px-4 py-8 text-center text-sm text-muted-foreground">
      {text}
    </div>
  );
}
