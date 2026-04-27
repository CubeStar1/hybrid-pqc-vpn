import { Globe, LockKeyhole, Route, Settings2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldContent, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type ProfileOption = {
  id: string;
  name: string;
};

type ProfileDetails = {
  gatewayHost: string;
  gatewayPort: number;
  tunnelCidr: string;
  mtu: number;
  supportedSuite: string;
};

type ProfileCardProps = {
  apiDraft: string;
  onApiDraftChange: (value: string) => void;
  onApplyEndpoint: () => void;
  isApplyingEndpoint: boolean;
  selectedProfileId: string;
  onProfileChange: (value: string) => void;
  profiles: ProfileOption[];
  profileDescription: string;
  profileDetails?: ProfileDetails;
};

export function ProfileCard({
  apiDraft,
  onApiDraftChange,
  onApplyEndpoint,
  isApplyingEndpoint,
  selectedProfileId,
  onProfileChange,
  profiles,
  profileDescription,
  profileDetails,
}: ProfileCardProps): React.JSX.Element {
  return (
    <Card className="border-border/70 bg-card/90 shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">Server & endpoint</CardTitle>
        <CardDescription>Pick a VPN profile and point the dashboard to the local agent.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <FieldGroup>
          <Field>
            <FieldLabel>Agent base URL</FieldLabel>
            <FieldContent>
              <Input value={apiDraft} onChange={(event) => onApiDraftChange(event.target.value)} />
              <FieldDescription>Usually the loopback API exposed by your local VPN agent.</FieldDescription>
            </FieldContent>
          </Field>
          <Field>
            <FieldLabel>VPN profile</FieldLabel>
            <FieldContent>
              <Select value={selectedProfileId} onValueChange={onProfileChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a profile" />
                </SelectTrigger>
                <SelectContent>
                  {profiles.map((profile) => (
                    <SelectItem key={profile.id} value={profile.id}>
                      {profile.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldDescription>{profileDescription}</FieldDescription>
            </FieldContent>
          </Field>
        </FieldGroup>

        <Button variant="outline" className="w-full rounded-full" onClick={onApplyEndpoint} disabled={isApplyingEndpoint}>
          <Settings2 />
          Apply endpoint
        </Button>

        <div className="grid gap-3 rounded-3xl border border-border/60 bg-muted/25 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground">
            <Globe className="size-4 text-primary" />
            Selected server details
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <InfoRow label="Gateway" value={profileDetails ? `${profileDetails.gatewayHost}:${profileDetails.gatewayPort}` : "Unavailable"} />
            <InfoRow label="Tunnel range" value={profileDetails?.tunnelCidr ?? "Unavailable"} />
            <InfoRow label="MTU" value={profileDetails ? String(profileDetails.mtu) : "Unavailable"} />
            <InfoRow label="Cipher suite" value={profileDetails?.supportedSuite ?? "Unavailable"} />
          </div>
          <div className="rounded-2xl border border-border/60 bg-background/80 px-4 py-3 text-sm text-muted-foreground">
            <div className="mb-1 flex items-center gap-2 text-foreground">
              <LockKeyhole className="size-4 text-primary" />
              Demo credentials
            </div>
            Username and password are currently fixed to the local demo account used by the agent.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-background/80 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-2 flex items-center gap-2 text-sm font-medium text-foreground">
        {label === "Tunnel range" ? <Route className="size-4 text-primary" /> : null}
        {value}
      </p>
    </div>
  );
}
