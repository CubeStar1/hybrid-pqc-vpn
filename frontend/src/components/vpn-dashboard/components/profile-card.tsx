import { Globe, Settings2 } from "lucide-react";

import { Button } from "@/components/ui/button";
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
    <section className="space-y-5">
      <h2 className="text-lg font-semibold text-foreground">Server & endpoint</h2>

      <FieldGroup>
        <Field>
          <FieldLabel>Agent base URL</FieldLabel>
          <FieldContent>
            <Input
              value={apiDraft}
              onChange={(event) => onApiDraftChange(event.target.value)}
            />
            <FieldDescription>Loopback API of the local VPN agent.</FieldDescription>
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
            <FieldDescription className="break-words">
              A profile is a saved gateway/tunnel target. {profileDescription}
            </FieldDescription>
          </FieldContent>
        </Field>
      </FieldGroup>

      <Button
        variant="outline"
        className="w-full rounded-full"
        onClick={onApplyEndpoint}
        disabled={isApplyingEndpoint}
      >
        <Settings2 />
        Apply endpoint
      </Button>

      {/* Server details — flat definition list, no individual cards */}
      <div className="space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Globe className="size-4 text-primary" />
          Server details
        </div>
        <dl className="grid gap-x-6 gap-y-2.5 text-sm sm:grid-cols-2">
          <DefItem label="Gateway" value={profileDetails ? `${profileDetails.gatewayHost}:${profileDetails.gatewayPort}` : "—"} />
          <DefItem label="Tunnel range" value={profileDetails?.tunnelCidr ?? "—"} />
          <DefItem label="MTU" value={profileDetails ? String(profileDetails.mtu) : "—"} />
          <DefItem label="Cipher suite" value={profileDetails?.supportedSuite ?? "—"} />
        </dl>
      </div>
    </section>
  );
}

function DefItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,92px)_minmax(0,1fr)] items-start gap-3 border-b border-border/40 pb-2 last:border-0">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="min-w-0 break-words text-right text-sm font-medium leading-snug text-foreground">
        {value}
      </dd>
    </div>
  );
}
