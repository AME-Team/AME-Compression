import {
  app,
  BrowserWindow,
  dialog,
  ipcMain,
  Menu,
  nativeImage,
  Notification,
  nativeTheme,
  session,
} from 'electron'
import * as path from 'path'
import * as fs from 'fs'
import { spawn, ChildProcess } from 'child_process'
import { fileURLToPath } from 'url'
import axios from 'axios'

// In ESM, __dirname is not available by default
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const isDev = process.env['NODE_ENV'] === 'development'
const API_PORT = 5000
const API_URL = `http://127.0.0.1:${API_PORT}/api`

let mainWindow: BrowserWindow | null = null
let flaskProcess: ChildProcess | null = null
let isQuitting = false
let isRestarting = false
let currentThemeMode = 'system'

nativeTheme.on('updated', () => {
  if (currentThemeMode === 'system' && mainWindow) {
    mainWindow.setBackgroundColor(getThemeBackgroundColor('system'))
  }
})

// Remove application menu for all platforms
Menu.setApplicationMenu(null)

async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await axios.get(`${API_URL}/health`, { timeout: 2000 })
    return response.status === 200
  } catch (_error) {
    return false
  }
}

interface BackendLaunchConfig {
  command: string
  args: string[]
  cwd: string
}

function resolveBackendLaunchConfig(projectRoot: string): BackendLaunchConfig {
  if (isDev) {
    let pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
    const venvPath = path.join(
      projectRoot,
      '.venv',
      process.platform === 'win32' ? 'Scripts' : 'bin',
      process.platform === 'win32' ? 'python.exe' : 'python',
    )

    if (fs.existsSync(venvPath)) {
      pythonCmd = venvPath
    } else {
      console.warn(`Venv not found at ${venvPath}, falling back to system python`)
    }

    return {
      command: pythonCmd,
      args: ['-m', 'backend', '--port', API_PORT.toString(), '--config', 'dev'],
      cwd: projectRoot,
    }
  }

  const backendRoot = path.join(process.resourcesPath, 'backend')
  const backendExecutable = path.join(
    backendRoot,
    process.platform === 'win32' ? 'ame-compression-backend.exe' : 'ame-compression-backend',
  )

  if (fs.existsSync(backendExecutable)) {
    return {
      command: backendExecutable,
      args: ['--port', API_PORT.toString(), '--config', 'prod'],
      cwd: backendRoot,
    }
  }

  // Fallback for non-packaged/partial environments.
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
  return {
    command: pythonCmd,
    args: ['-m', 'backend', '--port', API_PORT.toString(), '--config', 'prod'],
    cwd: projectRoot,
  }
}

function startFlask(): void {
  const projectRoot = isDev
    ? path.join(__dirname, '..', '..')
    : path.join(process.resourcesPath, 'app')

  const launchConfig = resolveBackendLaunchConfig(projectRoot)

  console.warn(`Starting backend with cwd: ${launchConfig.cwd} using ${launchConfig.command}`)

  flaskProcess = spawn(launchConfig.command, launchConfig.args, {
    cwd: launchConfig.cwd,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })

  flaskProcess.stdout?.on('data', (data) => {
    console.warn(`Flask: ${data}`)
  })

  flaskProcess.stderr?.on('data', (data) => {
    // Flask logs normal info to stderr in dev mode, so we use log/warn instead of error
    const message = data.toString()
    if (message.includes('ERROR') || message.includes('Exception')) {
      console.error(`Flask Error: ${message}`)
    } else {
      console.warn(`Flask (stderr): ${message}`)
    }
  })

  flaskProcess.on('close', (code) => {
    console.warn(`Flask process exited with code ${code}`)
    flaskProcess = null

    if (!isQuitting && !isRestarting) {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend-crashed')
      } else {
        app.quit()
      }
    }
  })

  flaskProcess.on('error', (err) => {
    console.error('Failed to start Flask process:', err)
    dialog.showErrorBox('Startup Error', `Failed to start the backend process: ${err.message}`)
  })
}

function getIconPath(): string {
  return isDev
    ? path.join(__dirname, '../public/icon.png')
    : path.join(process.resourcesPath, 'app', 'frontend', 'public', 'icon.png')
}

function getThemeBackgroundColor(mode: string): string {
  if (mode === 'dark') return '#111827'
  if (mode === 'system') {
    return nativeTheme.shouldUseDarkColors ? '#111827' : '#f9fafb'
  }
  return '#f9fafb'
}

function createWindow(): void {
  const iconImage = nativeImage.createFromPath(getIconPath())
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    icon: iconImage,
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#111827' : '#f9fafb',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: 'AME Compression',
  })

  mainWindow.setMenu(null)

  // Prevent default drag and drop behavior
  mainWindow.webContents.on('will-navigate', (event) => {
    event.preventDefault()
  })

  if (!isDev) {
    const cspHeader = [
      "default-src 'self'",
      "script-src 'self'",
      "style-src 'self'",
      "connect-src 'self' http://127.0.0.1:5000 http://localhost:5000",
      "img-src 'self' data:",
      "font-src 'self'",
    ].join('; ')

    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': [cspHeader],
        },
      })
    })
  }

  const startUrl = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../dist/index.html')}`

  void mainWindow.loadURL(startUrl)

  if (isDev) {
    mainWindow.webContents.openDevTools()
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function killFlask(): void {
  if (flaskProcess) {
    if (process.platform === 'win32') {
      // On Windows, childProcess.kill() might not kill the entire process tree
      // (especially with Flask's reloader). taskkill is more reliable.
      if (flaskProcess.pid) {
        const killer = spawn('taskkill', ['/pid', flaskProcess.pid.toString(), '/f', '/t'])
        killer.on('error', (err) => {
          console.error('Failed to execute taskkill:', err)
        })
      }
    } else {
      flaskProcess.kill()
    }
    flaskProcess = null
  }
}

// IPC Handlers
ipcMain.handle('get-api-url', () => {
  return API_URL
})

ipcMain.handle('get-backend-status', async () => {
  const isHealthy = await checkBackendHealth()
  return {
    running: !!flaskProcess,
    healthy: isHealthy,
    port: API_PORT,
  }
})

ipcMain.handle('restart-backend', async () => {
  if (flaskProcess) {
    const proc = flaskProcess
    isRestarting = true
    await new Promise<void>((resolve) => {
      proc.once('close', () => {
        isRestarting = false
        resolve()
      })
      killFlask()
    })
  }
  startFlask()
  return true
})

ipcMain.handle('set-theme-color', (_event, mode: string) => {
  currentThemeMode = mode
  if (mainWindow) {
    mainWindow.setBackgroundColor(getThemeBackgroundColor(mode))
  }
})

ipcMain.handle('send-notification', (_event, title: string, body: string) => {
  if (Notification.isSupported()) {
    const notification = new Notification({
      title,
      body,
      icon: getIconPath(),
    })
    notification.show()
  }
})

ipcMain.handle('select-file', async () => {
  if (!mainWindow) return null
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      {
        name: 'Media Files',
        extensions: ['mp4', 'mkv', 'avi', 'mov', 'mp3', 'wav', 'flac', 'm4a'],
      },
      { name: 'All Files', extensions: ['*'] },
    ],
  })
  if (result.canceled) return null
  return result.filePaths[0]
})

ipcMain.handle('select-files', async () => {
  if (!mainWindow) return null
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      {
        name: 'Media Files',
        extensions: ['mp4', 'mkv', 'avi', 'mov', 'mp3', 'wav', 'flac', 'm4a'],
      },
      { name: 'All Files', extensions: ['*'] },
    ],
  })
  if (result.canceled) return null
  return result.filePaths
})

ipcMain.on('backend-crash-response', (_event, action: string) => {
  if (action === 'restart') {
    startFlask()
  } else {
    app.quit()
  }
})

app.on('ready', () => {
  startFlask()
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

app.on('will-quit', () => {
  isQuitting = true
  killFlask()
})
