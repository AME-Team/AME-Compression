import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import Layout from './components/Layout'
import MediaView from './views/MediaView'
import type { MediaViewHandle } from './views/MediaView'
import type { MediaProfile } from './profiles'
import SettingsView from './views/SettingsView'
import FloatingBar from './components/FloatingBar'
import { useJobs } from './hooks/useJobs'
import { api, initializeApi } from './services/api'
import './App.css'

function App(): React.JSX.Element {
  const { i18n } = useTranslation()
  const [activeView, setActiveView] = useState('media')
  const [isReady, setIsReady] = useState(false)
  const { jobs, cancelJob } = useJobs()
  const [dismissedJobIds, setDismissedJobIds] = useState<Set<string>>(new Set())
  const mediaViewRef = useRef<MediaViewHandle>(null)

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
        const { language, appearance_mode } = response.data

        if (language) {
          void i18n.changeLanguage(language)
        }

        if (appearance_mode) {
          document.documentElement.setAttribute('data-theme', appearance_mode)
          void window.electronAPI?.setThemeColor(appearance_mode)
        }
      } catch (error) {
        console.error('Failed to initialize app settings', error)
      } finally {
        setIsReady(true)
      }
    }

    void initApp()
  }, [i18n])

  if (!isReady) {
    return <div className="loading-screen">Loading...</div>
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
        return <SettingsView />
      default:
        return (
          <div className="view-container">
            <h1>Coming Soon</h1>
            <p>This view is under development.</p>
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
    <>
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
    </>
  )
}

export default App
