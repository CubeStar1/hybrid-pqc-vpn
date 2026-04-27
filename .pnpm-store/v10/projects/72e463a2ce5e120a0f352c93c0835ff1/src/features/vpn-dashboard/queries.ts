"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { DEMO_CREDENTIALS } from "./constants";
import { connectDemoSession, disconnectDemoSession, getDashboardSnapshot, getElectronRuntime } from "./api";

export function useElectronRuntime() {
  return useQuery({
    queryKey: ["electron-runtime"],
    queryFn: getElectronRuntime,
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: Number.POSITIVE_INFINITY,
    retry: false,
  });
}

export function useDashboardSnapshot(apiBase: string) {
  return useQuery({
    queryKey: ["vpn-dashboard", apiBase],
    queryFn: () => getDashboardSnapshot(apiBase),
    enabled: Boolean(apiBase),
  });
}

export function useConnectSession(apiBase: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (profileId: string) =>
      connectDemoSession(apiBase, {
        profile_id: profileId,
        username: DEMO_CREDENTIALS.username,
        password: DEMO_CREDENTIALS.password,
      }),
    onSuccess: async (result) => {
      toast.success(result.message);
      await queryClient.invalidateQueries({ queryKey: ["vpn-dashboard", apiBase] });
    },
    onError: () => {
      toast.error("Connect failed. The Linux agent may be offline or missing Python dependencies.");
    },
  });
}

export function useDisconnectSession(apiBase: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      disconnectDemoSession(apiBase, {
        reason: "electron-dashboard",
      }),
    onSuccess: async (result) => {
      toast.success(result.message);
      await queryClient.invalidateQueries({ queryKey: ["vpn-dashboard", apiBase] });
    },
    onError: () => {
      toast.error("Disconnect failed. The local agent could not be reached.");
    },
  });
}
