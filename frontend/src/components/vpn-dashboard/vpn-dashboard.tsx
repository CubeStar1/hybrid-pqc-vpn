"use client";

import { useDeferredValue, useEffect, useState, useTransition } from "react";

import { DEFAULT_AGENT_API } from "./constants";
import { getCurrentProfile, getProfileDescription } from "./helpers";
import { useConnectSession, useDashboardSnapshot, useDisconnectSession, useElectronRuntime } from "./queries";
import { ConnectionHero } from "./components/connection-hero";
import { DashboardHeader } from "./components/dashboard-header";
import { ServerCard } from "./components/server-card";
import { SessionCard } from "./components/session-card";
import { StatTiles } from "./components/stat-tiles";

export function VpnDashboard(): React.JSX.Element {
  const [apiBase, setApiBase] = useState(DEFAULT_AGENT_API);
  const [apiDraft, setApiDraft] = useState(DEFAULT_AGENT_API);
  const [selectedProfileId, setSelectedProfileId] = useState("lab-gateway");
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
    <main className="min-h-screen bg-background">
      <div className="animate-fade-in mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6 sm:px-6 lg:px-8">
        <DashboardHeader isOnline={isOnline} />

        {/* ── Bento grid ──────────────────────────────────────────── */}
        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          {/* Row 1: Hero + Stats */}
          <div className="grid gap-3 lg:grid-cols-[1.4fr_0.6fr]  lg:col-span-2">
            <ConnectionHero
              isConnected={isConnected}
              isTunnelActive={Boolean(status?.current_session?.tunnel.active)}
              sessionState={sessionState}
              profileName={currentProfile?.name ?? "No profile selected"}
              canConnect={Boolean(selectedProfileId)}
              isBusy={isBusy}
              isRefreshing={dashboardQuery.isFetching}
              onConnect={() => connectMutation.mutate(selectedProfileId)}
              onDisconnect={() => disconnectMutation.mutate()}
              onRefresh={() => void dashboardQuery.refetch()}
            />

            <StatTiles
              isOnline={isOnline}
              oqsAvailable={Boolean(status?.oqs_available)}
              identityReady={Boolean(status?.server_identity_ready)}
              transcriptBytes={handshake?.transcript_bytes}
            />
          </div>

          {/* Row 2: Server + Session */}
          <div className="grid gap-3 lg:grid-cols-2 lg:col-span-2">
            <ServerCard
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

            <SessionCard
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
                    }
                  : null
              }
            />
          </div>
        </div>
      </div>
    </main>
  );
}
