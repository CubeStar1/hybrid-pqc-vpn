import { getDefaultAgentApi } from "./env";

export const DEFAULT_AGENT_API = getDefaultAgentApi();

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
  complete: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  in_progress: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  planned: "border-border bg-muted/40 text-muted-foreground",
} as const;
