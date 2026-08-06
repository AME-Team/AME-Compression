import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2 } from 'lucide-react'
import Layout from './components/Layout'
import MediaView from './views/MediaView'
import type { MediaViewHandle } from './views/MediaView'
import type { MediaProfile } from './profiles'
import SettingsView from './views/SettingsView'
import FloatingBar from './components/FloatingBar'
import ConfirmModal from './components/ConfirmModal'
import ToastProvider from './components/ToastProvider'
import CommandPalette from './components/CommandPalette'
import { useJobs } from './hooks/useJobs'
import { api, initializeApi } from './services/api'
import {
  useTheme,
  useAccentColor,
  useDocumentLang,
  isThemeMode,
  isAccentColor,
  resolveTheme,
  type ThemeMode,
  type AccentColor,
} from './hooks/useTheme'
import './App.css'

interface BackendErrorState {
  open: boolean
  title: string
  message: string
  variant: 'warning' | 'danger' | 'info'
  confirmLabel: string
  cancelLabel: string
  showCancel: boolean
  onConfirm: (() => void) | null
}

const INITIAL_BACKEND_ERROR: BackendErrorState = {
  open: false,
  title: '',
  message: '',
  variant: 'danger',
  confirmLabel: '',
  cancelLabel: '',
  showCancel: false,
  onConfirm: null,
}

function App(): React.JSX.Element {
  const { i18n, t } = useTranslation()
  const [activeView, setActiveView] = useState('media')
  const [isReady, setIsReady] = useState(false)
  const { jobs, cancelJob } = useJobs()
  const [dismissedJobIds, setDismissedJobIds] = useState<Set<string>>(new Set())
  const mediaViewRef = useRef<MediaViewHandle>(null)
  const [backendError, setBackendError] = useState<BackendErrorState>(INITIAL_BACKEND_ERROR)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  // 初期値は localStorage の保存値から lazy に読み込む（index.html の FOUC 防止
  // スクリプトと一致させる）。バックエンド取得完了後に保存済み設定で上書きされる。
  // プライバシーモード等でストレージが無効な場合は例外を握りつぶしてデフォルトに戻す。
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    try {
      const stored = localStorage.getItem('ame-theme-mode')
      return isThemeMode(stored) ? stored : 'system'
    } catch {
      return 'system'
    }
  })
  const [accentColor, setAccentColor] = useState<AccentColor>(() => {
    try {
      const stored = localStorage.getItem('ame-accent-color')
      return isAccentColor(stored) ? stored : 'trust-blue'
    } catch {
      return 'trust-blue'
    }
  })

  // persist は初回設定読み込み完了後 (isReady=true) のみ有効化する。
  // 起動時のデフォルト値で localStorage を上書きしないため。
  useTheme(themeMode, isReady)
  useAccentColor(accentColor, isReady)
  useDocumentLang(i18n.resolvedLanguage ?? 'en')

  // SettingsView のプレビュー（未保存）が data-theme / data-accent に残らないよう、
  // ビュー切替のたびに保存済みの外観設定を再適用する（App を単一の真実源にする）。
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolveTheme(themeMode))
    document.documentElement.setAttribute('data-accent', accentColor)
  }, [activeView, themeMode, accentColor])

  const [compressionDisabled, setCompressionDisabled] = useState(true)
  const [compressionLoading, setCompressionLoading] = useState(false)
  const [compressionInitiated, setCompressionInitiated] = useState(false)
  const [currentSettings, setCurrentSettings] = useState<Omit<MediaProfile, 'name'> | null>(null)

  const visibleJobs = jobs.filter((job) => !dismissedJobIds.has(job.id))
  const hasRunningJobs = jobs.some((j) => j.status === 'running' || j.status === 'starting')
  const isCompressing = compressionInitiated || compressionLoading || hasRunningJobs

  useEffect(() => {
    if (compressionInitiated && hasRunningJobs) {
      setCompressionInitiated(false)
    }
  }, [compressionInitiated, hasRunningJobs])

  const handleDismissJob = (id: string): void => {
    setDismissedJobIds((prev) => {
      const next = new Set(prev)
      next.add(id)
      return next
    })
  }

  const cleanupDismissed = useCallback(() => {
    setDismissedJobIds((prev) => {
      if (prev.size === 0) return prev
      const currentJobIds = new Set(jobs.map((job) => job.id))
      const next = new Set<string>()
      for (const id of prev) {
        if (currentJobIds.has(id)) {
          next.add(id)
        }
      }
      if (next.size === prev.size) return prev
      return next
    })
  }, [jobs])

  useEffect(() => {
    cleanupDismissed()
  }, [cleanupDismissed])

  useEffect(() => {
    const initApp = async (): Promise<void> => {
      try {
        await initializeApi()

        const response = await api.get('/settings')
        const { language, appearance_mode, accent_color } = response.data

        if (language) {
          void i18n.changeLanguage(language)
        }

        if (isThemeMode(appearance_mode)) {
          setThemeMode(appearance_mode)
        }

        if (isAccentColor(accent_color)) {
          setAccentColor(accent_color)
        }
      } catch (error) {
        console.error('Failed to initialize app settings', error)
      } finally {
        setIsReady(true)
      }
    }

    void initApp()
  }, [i18n])

  useEffect(() => {
    const cleanup = window.electronAPI?.onBackendCrashed(() => {
      setBackendError({
        open: true,
        title: t('errors.backend_crash_title'),
        message: t('errors.backend_crash_message'),
        variant: 'danger',
        confirmLabel: t('common.restart'),
        cancelLabel: t('common.exit'),
        showCancel: true,
        onConfirm: () => {
          setBackendError(INITIAL_BACKEND_ERROR)
          window.electronAPI?.respondBackendCrash('restart')
        },
      })
    })

    return () => {
      cleanup?.()
    }
  }, [t])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  const handleAppearanceChange = useCallback((mode: ThemeMode, accent: AccentColor): void => {
    setThemeMode(mode)
    setAccentColor(accent)
  }, [])

  if (!isReady) {
    return (
      <div className="loading-screen" role="status" aria-live="polite">
        <Loader2 size={20} className="spin" />
      </div>
    )
  }

  const renderView = (): React.JSX.Element => {
    switch (activeView) {
      case 'media':
        return (
          <MediaView
            ref={mediaViewRef}
            onStateChange={({ inputPaths, loading, settings }) => {
              setCompressionDisabled(inputPaths.length === 0)
              setCompressionLoading(loading)
              setCurrentSettings(settings)
            }}
          />
        )
      case 'settings':
        return <SettingsView onAppearanceChange={handleAppearanceChange} />
      default:
        return (
          <div className="view-container">
            <header className="view-header">
              <h1>{t('coming_soon.title')}</h1>
              <p>{t('coming_soon.description')}</p>
            </header>
          </div>
        )
    }
  }

  const handleStartCompression = (): void => {
    setCompressionInitiated(true)
    void mediaViewRef.current?.startCompression()
  }

  const handleCancelJob = (id: string): void => {
    void cancelJob(id)
  }

  const isMediaView = activeView === 'media'

  return (
    <ToastProvider>
      <Layout activeView={activeView} onViewChange={setActiveView}>
        {renderView()}
      </Layout>
      {isMediaView && currentSettings && (
        <FloatingBar
          onStartCompression={handleStartCompression}
          compressionDisabled={compressionDisabled}
          isCompressing={isCompressing}
          jobs={visibleJobs}
          onCancelJob={handleCancelJob}
          onDismissJob={handleDismissJob}
          currentSettings={currentSettings}
          onApplyProfile={(settings) => {
            mediaViewRef.current?.applyProfile(settings)
          }}
          onApplyDefaults={() => {
            mediaViewRef.current?.applyDefaults()
          }}
        />
      )}
      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => {
          setCommandPaletteOpen(false)
        }}
        onNavigate={setActiveView}
        onStartCompression={handleStartCompression}
        onApplyDefaults={() => {
          mediaViewRef.current?.applyDefaults()
        }}
      />
      <ConfirmModal
        open={backendError.open}
        title={backendError.title}
        message={backendError.message}
        confirmLabel={backendError.confirmLabel}
        cancelLabel={backendError.cancelLabel}
        variant={backendError.variant}
        showCancel={backendError.showCancel}
        onConfirm={backendError.onConfirm ?? (() => undefined)}
        onCancel={() => {
          if (backendError.showCancel) {
            window.electronAPI?.respondBackendCrash('exit')
          }
          setBackendError(INITIAL_BACKEND_ERROR)
        }}
      />
    </ToastProvider>
  )
}

export default App
