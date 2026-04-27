import { Activity, Binary, Fingerprint, ShieldCheck } from "lucide-react";

import { QuickStat } from "./quick-stat";

type NetworkOverviewProps = {
  isOnline: boolean;
  oqsAvailable: boolean;
  identityReady: boolean;
  transcriptBytes?: number;
};

export function NetworkOverview({
  isOnline,
  oqsAvailable,
  identityReady,
  transcriptBytes,
}: NetworkOverviewProps): React.JSX.Element {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <QuickStat
        icon={Activity}
        label="Agent"
        value={isOnline ? "Online" : "Offline"}
        hint={isOnline ? "The local API is responding." : "The dashboard cannot reach the agent."}
      />
      <QuickStat
        icon={Binary}
        label="PQC"
        value={oqsAvailable ? "Ready" : "Unavailable"}
        hint={oqsAvailable ? "Hybrid crypto support is loaded." : "liboqs support is not available yet."}
      />
      <QuickStat
        icon={Fingerprint}
        label="Identity"
        value={identityReady ? "Pinned" : "Pending"}
        hint={identityReady ? "Server identity is ready." : "Server identity is not fully configured."}
      />
      <QuickStat
        icon={ShieldCheck}
        label="Handshake"
        value={transcriptBytes ? `${transcriptBytes} B` : "--"}
        hint="Latest handshake transcript size."
      />
    </section>
  );
}
