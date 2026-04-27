import { Cpu, LaptopMinimal, Network, Server, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
    <Card className="border-border/70 bg-card/90 shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">Details</CardTitle>
        <CardDescription>Keep advanced session and runtime information available without crowding the main screen.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="session">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="session">Session</TabsTrigger>
            <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
          </TabsList>

          <TabsContent value="session" className="mt-4 space-y-4">
            {session ? (
              <>
                <div className="flex items-center justify-between rounded-3xl border border-border/60 bg-muted/25 p-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Active tunnel</p>
                    <p className="mt-2 text-lg font-semibold capitalize text-foreground">{session.state}</p>
                  </div>
                  <Badge variant="outline" className="rounded-full">
                    {session.suite}
                  </Badge>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <DetailRow icon={Network} label="Profile" value={session.profileId} />
                  <DetailRow icon={LaptopMinimal} label="Username" value={session.username} />
                  <DetailRow icon={Cpu} label="PQC" value={session.pqcEnabled ? "Enabled" : "Disabled"} />
                  <DetailRow
                    icon={ShieldAlert}
                    label="Transcript"
                    value={session.transcriptHash?.slice(0, 16) ?? "Pending"}
                  />
                </div>
                {session.notes.length ? (
                  <div className="space-y-2 rounded-3xl border border-border/60 bg-background/80 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Notes</p>
                    {session.notes.map((note) => (
                      <p key={note} className="text-sm leading-6 text-foreground">
                        {note}
                      </p>
                    ))}
                  </div>
                ) : null}
              </>
            ) : (
              <EmptyState text="No active session yet. Connect to a profile to see tunnel details here." />
            )}
          </TabsContent>

          <TabsContent value="diagnostics" className="mt-4 space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <DetailRow icon={Server} label="Agent API" value={runtime?.defaultAgentApi ?? "Unavailable"} />
              <DetailRow icon={Network} label="Gateway API" value={runtime?.defaultGatewayApi ?? "Unavailable"} />
              <DetailRow icon={LaptopMinimal} label="Electron" value={runtime?.electronVersion ?? "Browser preview"} />
              <DetailRow icon={Cpu} label="Node" value={runtime?.nodeVersion ?? "Unavailable"} />
            </div>
            <Separator />
            <div className="space-y-2 rounded-3xl border border-border/60 bg-background/80 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Platform</p>
              <p className="text-sm font-medium text-foreground">{runtime?.platform ?? "web"}</p>
              {(runtime?.notes ?? ["Runtime notes are not available yet."]).map((note) => (
                <p key={note} className="text-sm leading-6 text-muted-foreground">
                  {note}
                </p>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
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
    <div className="rounded-2xl border border-border/60 bg-background/80 px-4 py-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        <Icon className="size-3.5 text-primary" />
        {label}
      </div>
      <p className="mt-2 break-all text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-border/70 bg-muted/20 px-4 py-8 text-sm text-muted-foreground">
      {text}
    </div>
  );
}
