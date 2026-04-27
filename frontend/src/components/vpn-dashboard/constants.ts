export const DEFAULT_AGENT_API = "http://127.0.0.1:8765";

export const DEMO_CREDENTIALS = {
  username: "demo",
  password: "demo-vpn-2026",
} as const;

export const STATUS_LABEL = {
  complete: "Complete",
  in_progress: "In Progress",
  planned: "Planned",
} as const;

export const PHASE_TONE = {
  complete: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
  in_progress: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  planned: "border-white/12 bg-white/6 text-slate-100",
} as const;
