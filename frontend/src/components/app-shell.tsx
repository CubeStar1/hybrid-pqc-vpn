"use client";

import { ThemeToggle } from "@/components/theme-toggle";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export function AppShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-auto bg-background">
        <header className="sticky top-0 z-20 border-b border-border/60 bg-background/85 backdrop-blur rounded-2xl">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <SidebarTrigger />
              <Separator orientation="vertical" className="h-6" />
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-muted-foreground">
                  Cryptography Network Security
                </p>
                <h1 className="truncate text-sm font-semibold text-foreground sm:text-base">
                  Hybrid VPN Control Center
                </h1>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </header>
        <div className="flex-1">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
