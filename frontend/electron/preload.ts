import { contextBridge, ipcRenderer, webUtils } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  selectFile: () => ipcRenderer.invoke('select-file'),
  selectFiles: () => ipcRenderer.invoke('select-files'),
  sendNotification: (title: string, body: string) =>
    ipcRenderer.invoke('send-notification', title, body),
  setThemeColor: (mode: string) => ipcRenderer.invoke('set-theme-color', mode),
  getPathForFile: (file: File) => {
    const utils = webUtils as { getPathForFile?: (f: File) => string }
    return utils.getPathForFile?.(file)
  },
  onBackendCrashed: (callback: () => void) => {
    const handler = (): void => {
      callback()
    }
    ipcRenderer.on('backend-crashed', handler)
    return () => ipcRenderer.removeListener('backend-crashed', handler)
  },
  respondBackendCrash: (action: string) => {
    ipcRenderer.send('backend-crash-response', action)
  },
})
