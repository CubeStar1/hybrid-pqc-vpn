"use client";

import { useDeferredValue, useEffect, useState, useTransition } from "react";

import { DEFAULT_AGENT_API } from "./constants";
import { getCurrentProfile, getProfileDescription } from "./helpers";
import { useConnectSession, useDashboardSnapshot, useDisconnectSession, useElectronRuntime } from "./queries";
import { ActivityPanel } from "./components/activity-panel";
import { ConnectionPanel } from "./components/connection-panel";
import { DashboardHeader } from "./components/dashboard-header";
import { NetworkOverview } from "./components/network-overview";
import { ProfileCard } from "./components/profile-card";

export function VpnDashboard(): React.JSX.Element {
  const [apiBase, setApiBase] = useState(DEFAULT_AGENT_API);
  const [apiDraft, setApiDraft] = useState(DEFAULT_AGENT_API);
  const [selectedProfileId, setSelectedProfileId] = useState("lab-gateway");
  const [connectMessage, setConnectMessage] = useState("VPN agent has not been queried yet.");
  const [isApplyingEndpoint, startApplyEndpoint] = useTransition();

  const deferredApiBase = useDeferredValue(apiBase);
  const runtimeQuery = useElectronRuntime();
  const dashboardQuery = useDashboardSnapshot(deferredApiBase);
  const connectMutation = useConnectSession(deferredApiBase);
  const disconnectMutation = useDisconnectSession(deferredApiBase);

  useEffect(() => {
    if (runtimeQuery.data?.defaultAgentApi) {
      setApiBase(runtimeQuery.data.defaultAgentApi);
      setApiDraft(runtimeQuery.data.defaultAgentApi);
    }
  }, [runtimeQuery.data?.defaultAgentApi]);

  useEffect(() => {
    const firstProfileId = dashboardQuery.data?.profiles[0]?.id;
    if (firstProfileId) {
      setSelectedProfileId((current) => current || firstProfileId);
    }
  }, [dashboardQuery.data?.profiles]);

  useEffect(() => {
    if (dashboardQuery.isSuccess) {
      setConnectMessage("Local VPN agent is reachable and ready.");
      return;
    }

    if (dashboardQuery.isError) {
      setConnectMessage("VPN agent is offline. Start the local control API and refresh.");
    }
  }, [dashboardQuery.isError, dashboardQuery.isSuccess]);

  const status = dashboardQuery.data?.status;
  const handshake = dashboardQuery.data?.handshake;
  const profiles = dashboardQuery.data?.profiles ?? [];
  const currentProfile = getCurrentProfile(profiles, selectedProfileId);
  const isConnected = status?.current_session?.state === "connected";
  const sessionState = status?.current_session?.state ?? (dashboardQuery.isFetching ? "checking" : "disconnected");
  const isBusy = connectMutation.isPending || disconnectMutation.isPending;
  const profileOptions = profiles.length ? profiles : [{ id: "lab-gateway", name: "RVCE Lab Gateway" }];
  const isOnline = Boolean(status);

  return (
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.08),transparent_50%)] dark:bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.12),transparent_50%)]">
      <div className="animate-fade-in mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
        <DashboardHeader isOnline={isOnline} />

        <NetworkOverview
          isOnline={isOnline}
          oqsAvailable={Boolean(status?.oqs_available)}
          identityReady={Boolean(status?.server_identity_ready)}
          transcriptBytes={handshake?.transcript_bytes}
        />

        <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
          <ConnectionPanel
            isConnected={isConnected}
            isTunnelActive={Boolean(status?.current_session?.tunnel.active)}
            sessionState={sessionState}
            profileName={currentProfile?.name ?? "No profile selected"}
            connectMessage={connectMessage}
            lastHandshake={
              handshake
                ? `${handshake.authentication_verified ? "Verified" : "Pending"} · ${
                    handshake.oqs_available ? "PQC ready" : "PQC unavailable"
                  }`
                : "Awaiting handshake data."
            }
            canConnect={Boolean(selectedProfileId)}
            isBusy={isBusy}
            isRefreshing={dashboardQuery.isFetching}
            onConnect={() => {
              setConnectMessage("Requesting a VPN session from the local agent.");
              connectMutation.mutate(selectedProfileId);
            }}
            onDisconnect={() => {
              setConnectMessage("Disconnecting the current VPN session.");
              disconnectMutation.mutate();
            }}
            onRefresh={() => void dashboardQuery.refetch()}
          />

          <ProfileCard
            apiDraft={apiDraft}
            onApiDraftChange={setApiDraft}
            onApplyEndpoint={() => startApplyEndpoint(() => setApiBase(apiDraft))}
            isApplyingEndpoint={isApplyingEndpoint}
            selectedProfileId={selectedProfileId}
            onProfileChange={setSelectedProfileId}
            profiles={profileOptions}
            profileDescription={getProfileDescription(currentProfile)}
            profileDetails={
              currentProfile
                ? {
                    gatewayHost: currentProfile.gateway_host,
                    gatewayPort: currentProfile.gateway_port,
                    tunnelCidr: currentProfile.tunnel_cidr,
                    mtu: currentProfile.mtu,
                    supportedSuite: currentProfile.supported_suite,
                  }
                : undefined
            }
          />
        </div>

        <ActivityPanel
          session={
            status?.current_session
              ? {
                  profileId: status.current_session.profile_id,
                  username: status.current_session.username,
                  suite: status.current_session.suite,
                  state: status.current_session.state,
                  tunnelActive: status.current_session.tunnel.active,
                  remoteEndpoint: status.current_session.tunnel.remote_endpoint,
                  localAddress: status.current_session.tunnel.local_address,
                  transcriptHash: status.current_session.transcript_hash_hex,
                  pqcEnabled: status.current_session.pqc_enabled,
                  notes: status.current_session.notes,
                }
              : null
          }
          runtime={runtimeQuery.data}
        />
      </div>
    </main>
  );
}
