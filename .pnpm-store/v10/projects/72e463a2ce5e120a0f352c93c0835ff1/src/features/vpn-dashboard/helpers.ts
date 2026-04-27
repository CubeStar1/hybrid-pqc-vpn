import type { Profile } from "./types";

export function getCurrentProfile(profiles: Profile[], selectedProfileId: string) {
  return profiles.find((profile) => profile.id === selectedProfileId);
}

export function getProfileDescription(profile?: Profile) {
  if (!profile) {
    return "The local agent will publish available profiles here.";
  }

  return `${profile.gateway_host}:${profile.gateway_port} | ${profile.tunnel_cidr} | MTU ${profile.mtu}`;
}
