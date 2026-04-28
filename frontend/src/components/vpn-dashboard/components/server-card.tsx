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

type ServerCardProps = {
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

export function ServerCard({
  apiDraft,
  onApiDraftChange,
  onApplyEndpoint,
  isApplyingEndpoint,
  selectedProfileId,
  onProfileChange,
  profiles,
  profileDescription,
  profileDetails,
}: ServerCardProps): React.JSX.Element {
  return (
    <div className="bento-card p-5 space-y-4 animate-tile-in" style={{ animationDelay: "60ms" }}>
      <div className="flex items-center gap-2 mb-1">
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Globe className="size-4" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">Server & Endpoint</h3>
      </div>

      <FieldGroup>
        <Field>
          <FieldLabel>Agent base URL</FieldLabel>
          <FieldContent>
            <Input
              value={apiDraft}
              onChange={(event) => onApiDraftChange(event.target.value)}
              className="font-mono text-xs"
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
              {profileDescription}
            </FieldDescription>
          </FieldContent>
        </Field>
      </FieldGroup>

      <Button
        variant="outline"
        size="sm"
        className="w-full rounded-full"
        onClick={onApplyEndpoint}
        disabled={isApplyingEndpoint}
      >
        <Settings2 className="size-3.5" />
        Apply endpoint
      </Button>

      {/* Server details grid */}
      {profileDetails && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 pt-2 border-t border-border/40">
          <DetailItem label="Gateway" value={`${profileDetails.gatewayHost}:${profileDetails.gatewayPort}`} />
          <DetailItem label="Tunnel range" value={profileDetails.tunnelCidr} />
          <DetailItem label="MTU" value={String(profileDetails.mtu)} />
          <DetailItem label="Cipher suite" value={profileDetails.supportedSuite} mono />
        </div>
      )}
    </div>
  );
}

function DetailItem({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <p className="text-[10px] uppercase tracking-widest text-muted-foreground/70">{label}</p>
      <p className={`text-sm font-medium text-foreground truncate ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </p>
    </div>
  );
}
