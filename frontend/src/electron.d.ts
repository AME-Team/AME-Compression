export interface BackendStatus {
  running: boolean
  healthy: boolean
  port: number
}

export interface IElectronAPI {
  platform: string
  getApiUrl: () => Promise<string>
  getBackendStatus: () => Promise<BackendStatus>
  restartBackend: () => Promise<boolean>
  selectFile: () => Promise<string | null>
  selectFiles: () => Promise<string[] | null>
  sendNotification: (title: string, body: string) => Promise<void>
  setThemeColor: (mode: string) => Promise<void>
  getPathForFile?: (file: File) => string | undefined
  onBackendCrashed: (callback: () => void) => () => void
  onBackendStartupError: (callback: (message: string) => void) => () => void
  respondBackendCrash: (action: string) => void
}

declare global {
  interface Window {
    electronAPI?: IElectronAPI
  }

  interface File {
    path?: string
  }
}
