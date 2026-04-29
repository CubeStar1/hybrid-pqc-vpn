"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield } from "lucide-react";

import { sidebarGroups } from "@/lib/config/sidebar";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";

export function AppSidebar(): React.JSX.Element {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader className="gap-3 px-3 py-4 group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:px-2">
        <div className="flex items-center gap-3 rounded-xl border border-sidebar-border/70 bg-sidebar-primary px-3 py-3 text-sidebar-primary-foreground transition-all group-data-[collapsible=icon]:size-10 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:rounded-2xl group-data-[collapsible=icon]:px-0">
          <div className="flex size-10 items-center justify-center rounded-lg bg-sidebar-primary-foreground/12 transition-all group-data-[collapsible=icon]:size-8">
            <Shield className="size-5" />
          </div>
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-sm font-semibold">Hybrid PQC VPN</p>
            <p className="truncate text-xs text-sidebar-primary-foreground/70">
              Control Center
            </p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2 pb-4 group-data-[collapsible=icon]:px-1">
        {sidebarGroups.map((group) => (
          <SidebarGroup
            key={group.label}
            className="group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:px-0"
          >
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={item.href === pathname}
                      tooltip={item.title}
                      className="group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:justify-center"
                    >
                      <Link href={item.href}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
