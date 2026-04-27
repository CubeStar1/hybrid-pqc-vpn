const DEFAULT_AGENT_API = "http://127.0.0.1:8765";
const DEFAULT_GATEWAY_API = "http://127.0.0.1:9876";

export function getDefaultAgentApi(): string {
  return process.env.NEXT_PUBLIC_HYBRID_VPN_AGENT_API_URL || DEFAULT_AGENT_API;
}

export function getDefaultGatewayApi(): string {
  return process.env.NEXT_PUBLIC_HYBRID_VPN_GATEWAY_API_URL || DEFAULT_GATEWAY_API;
}
