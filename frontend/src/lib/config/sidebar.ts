import type { LucideIcon } from "lucide-react";
import { Activity, FolderKanban, LayoutDashboard, Network, PlugZap, ShieldCheck } from "lucide-react";

export type SidebarItem = {
  title: string;
  href: string;
  icon: LucideIcon;
  description: string;
};

export type SidebarGroup = {
  label: string;
  items: SidebarItem[];
};

export const sidebarGroups: SidebarGroup[] = [
  {
    label: "Control Center",
    items: [
      {
        title: "Dashboard",
        href: "/",
        icon: LayoutDashboard,
        description: "Overview of the hybrid VPN workspace.",
      },
      {
        title: "Connection",
        href: "/#connection",
        icon: PlugZap,
        description: "Connect, disconnect, and refresh session state.",
      },
      {
        title: "Telemetry",
        href: "/#stats",
        icon: Activity,
        description: "Track runtime health and handshake readiness.",
      },
    ],
  },
  {
    label: "Workspace",
    items: [
      {
        title: "Profiles",
        href: "/#profiles",
        icon: FolderKanban,
        description: "Browse gateway profiles and endpoint settings.",
      },
      {
        title: "Session",
        href: "/#session",
        icon: ShieldCheck,
        description: "Inspect the active tunnel and crypto details.",
      },
      {
        title: "Architecture",
        href: "/architecture",
        icon: Network,
        description: "Detailed visualization of the VPN and encryption flow.",
      },
    ],
  },
];
