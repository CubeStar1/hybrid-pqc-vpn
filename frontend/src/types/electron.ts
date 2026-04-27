export type ElectronRuntimeContext = {
  platform: string;
  arch: string;
  nodeVersion: string;
  electronVersion: string;
  chromeVersion: string;
  linuxVmRecommended: boolean;
  defaultAgentApi: string;
  defaultGatewayApi: string;
  notes: string[];
};
