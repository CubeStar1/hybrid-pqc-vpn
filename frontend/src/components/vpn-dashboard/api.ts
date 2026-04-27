import type {
  ConnectRequest,
  DashboardSnapshot,
  DisconnectRequest,
  ElectronRuntimeContext,
  HandshakeDemo,
  MessageResponse,
  Profile,
  ProjectSnapshot,
  RuntimeStatus,
} from "./types";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getElectronRuntime(): Promise<ElectronRuntimeContext> {
  if (typeof window === "undefined") {
    throw new Error("Electron runtime is only available in the client");
  }

  return window.electron.runtime.getContext();
}

export async function getDashboardSnapshot(apiBase: string): Promise<DashboardSnapshot> {
  const [status, snapshot, profiles, handshake] = await Promise.all([
    fetchJson<RuntimeStatus>(`${apiBase}/status`),
    fetchJson<ProjectSnapshot>(`${apiBase}/snapshot`),
    fetchJson<Profile[]>(`${apiBase}/profiles`),
    fetchJson<HandshakeDemo>(`${apiBase}/demo/handshake`, { method: "POST" }),
  ]);

  return {
    status,
    snapshot,
    profiles,
    handshake,
  };
}

export async function connectDemoSession(
  apiBase: string,
  payload: ConnectRequest,
): Promise<MessageResponse> {
  return fetchJson<MessageResponse>(`${apiBase}/connect`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function disconnectDemoSession(
  apiBase: string,
  payload: DisconnectRequest,
): Promise<MessageResponse> {
  return fetchJson<MessageResponse>(`${apiBase}/disconnect`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
