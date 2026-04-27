import type { ElectronRuntimeContext } from "@/types/electron";

export type { ElectronRuntimeContext };

export type PhaseStatus = {
  name: string;
  status: "complete" | "in_progress" | "planned";
  summary: string;
};

export type RuntimeStatus = {
  service: string;
  version: string;
  oqs_available: boolean;
  server_identity_ready: boolean;
  runtime: {
    mode: string;
    platform: string;
    linux_vm_target: boolean;
    tun_interface?: string | null;
    control_api?: string | null;
    notes: string[];
  };
  phases: PhaseStatus[];
  current_session?: {
    session_id: string;
    state: string;
    username: string;
    profile_id: string;
    suite: string;
    transcript_hash_hex?: string | null;
    pqc_enabled: boolean;
    notes: string[];
  } | null;
};

export type ProjectSnapshot = {
  title: string;
  summary: string;
  architecture: {
    title: string;
    description: string;
    details: string[];
  }[];
  phases: PhaseStatus[];
};

export type Profile = {
  id: string;
  name: string;
  gateway_host: string;
  gateway_port: number;
  tunnel_cidr: string;
  mtu: number;
  supported_suite: string;
};

export type HandshakeDemo = {
  oqs_available: boolean;
  authentication_verified: boolean;
  transcript_bytes: number;
  mlkem_public_bytes?: number | null;
  mlkem_ciphertext_bytes?: number | null;
};

export type ConnectRequest = {
  profile_id: string;
  username: string;
  password: string;
};

export type DisconnectRequest = {
  reason: string;
};

export type MessageResponse = {
  message: string;
};

export type DashboardSnapshot = {
  status: RuntimeStatus;
  snapshot: ProjectSnapshot;
  profiles: Profile[];
  handshake: HandshakeDemo;
};
