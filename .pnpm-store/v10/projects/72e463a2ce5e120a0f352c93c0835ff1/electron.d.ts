import type { ElectronRuntimeContext } from "./src/types/electron";

declare global {
  interface Window {
    electron: {
      runtime: {
        getContext: () => Promise<ElectronRuntimeContext>;
      };
      ipcRenderer: {
        send: (channel: string, ...args: any[]) => void;
        on: (channel: string, listener: (...args: any[]) => void) => void;
      };
    };
  }
}

export {};
