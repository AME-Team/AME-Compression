import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Play, Loader2, Save, X, Download, RotateCcw, Trash2 } from 'lucide-react'
import type { Job } from '../types'
import type { MediaProfile } from '../profiles'
import { loadProfiles, saveProfiles } from '../profiles'
import { ProgressPanel } from './ProgressPanel'
import ConfirmModal from './ConfirmModal'

function useClickOutside(
  ref: React.RefObject<HTMLDivElement | null>,
  isOpen: boolean,
  onClose: () => void,
  triggerSelector: string,
): void {
  useEffect(() => {
    if (!isOpen) return
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        ref.current &&
        e.target instanceof Element &&
        !ref.current.contains(e.target) &&
        !e.target.closest(triggerSelector)
      ) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [ref, isOpen, onClose, triggerSelector])
}

interface FloatingBarProps {
  onStartCompression: () => void
  compressionDisabled: boolean
  isCompressing: boolean
  jobs: Job[]
  onCancelJob: (id: string) => void
  onDismissJob: (id: string) => void
  currentSettings: Omit<MediaProfile, 'name'>
  onApplyProfile: (settings: Omit<MediaProfile, 'name'>) => void
  onApplyDefaults: () => void
}

interface ConfirmState {
  open: boolean
  title: string
  message: string
  variant: 'warning' | 'danger' | 'info'
  confirmLabel: string
  onConfirm: (() => void) | null
}

const INITIAL_CONFIRM_STATE: ConfirmState = {
  open: false,
  title: '',
  message: '',
  variant: 'info',
  confirmLabel: '',
  onConfirm: null,
}

interface ProfileModalContentProps {
  t: TFunction
  currentSettings: Omit<MediaProfile, 'name'>
  onApplyProfile: (settings: Omit<MediaProfile, 'name'>) => void
  onApplyDefaults: () => void
  onClose: () => void
  onNotify: (message: string) => void
  setConfirmState: React.Dispatch<React.SetStateAction<ConfirmState>>
}

const ProfileModalContent: React.FC<ProfileModalContentProps> = ({
  t,
  currentSettings,
  onApplyProfile,
  onApplyDefaults,
  onClose,
  onNotify,
  setConfirmState,
}) => {
  const [profiles, setProfiles] = useState<MediaProfile[]>(loadProfiles)
  const [profileName, setProfileName] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [saveFlash, setSaveFlash] = useState(false)

  const showMessage = useCallback((msg: string): void => {
    setStatusMessage(msg)
    setTimeout(() => {
      setStatusMessage('')
    }, 3000)
  }, [])

  useEffect(() => {
    if (!saveFlash) return
    const timer = setTimeout(() => {
      setSaveFlash(false)
    }, 200)
    return (): void => {
      clearTimeout(timer)
    }
  }, [saveFlash])

  const handleSave = (): void => {
    const name = profileName.trim()
    if (!name) {
      showMessage(t('profile.name_required'))
      return
    }
    const existingIndex = profiles.findIndex((p) => p.name === name)
    if (existingIndex >= 0) {
      setConfirmState({
        open: true,
        title: t('profile.overwrite_title'),
        message: t('profile.overwrite_confirm', { name }),
        variant: 'warning',
        confirmLabel: t('common.overwrite'),
        onConfirm: () => {
          setConfirmState(INITIAL_CONFIRM_STATE)
          const updated = [...profiles]
          updated[existingIndex] = { ...currentSettings, name }
          setProfiles(updated)
          saveProfiles(updated)
          showMessage(t('profile.saved', { name }))
          setProfileName('')
          setSaveFlash(true)
        },
      })
      return
    }
    const updated = [...profiles, { ...currentSettings, name }]
    setProfiles(updated)
    saveProfiles(updated)
    showMessage(t('profile.saved', { name }))
    setProfileName('')
    setSaveFlash(true)
  }

  const handleLoad = (profile: MediaProfile): void => {
    setConfirmState({
      open: true,
      title: t('profile.load_title'),
      message: t('profile.load_confirm', { name: profile.name }),
      variant: 'info',
      confirmLabel: t('profile.load'),
      onConfirm: () => {
        setConfirmState(INITIAL_CONFIRM_STATE)
        const { name: _name, ...settings } = profile
        onApplyProfile(settings)
        onNotify(t('profile.loaded', { name: _name }))
        onClose()
      },
    })
  }

  const handleDelete = (name: string): void => {
    const updated = profiles.filter((p) => p.name !== name)
    setProfiles(updated)
    saveProfiles(updated)
    showMessage(t('profile.deleted', { name }))
  }

  const handleDefaults = (): void => {
    onApplyDefaults()
    showMessage(t('profile.defaults_loaded'))
  }

  return (
    <div>
      <div className="profile-bar">
        <input
          type="text"
          value={profileName}
          onChange={(e) => {
            setProfileName(e.target.value)
          }}
          placeholder={t('profile.name_placeholder')}
          className={`profile-name-input${saveFlash ? ' save-flash' : ''}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave()
          }}
          aria-label={t('profile.name_placeholder')}
        />
        <button
          className="secondary-button profile-btn"
          onClick={handleSave}
          title={t('profile.save')}
          aria-label={t('profile.save')}
        >
          <Save size={14} />
        </button>
        <button
          className="secondary-button profile-btn"
          onClick={handleDefaults}
          title={t('profile.load_defaults')}
          aria-label={t('profile.load_defaults')}
        >
          <RotateCcw size={14} />
        </button>
      </div>
      {profiles.length > 0 ? (
        <div className="profile-list" role="list" aria-label={t('profile.title')}>
          {profiles.map((profile) => (
            <div key={profile.name} className="profile-item" role="listitem">
              <span className="profile-item-name" title={profile.name}>
                {profile.name}
              </span>
              <span className="profile-item-type">
                {profile.mediaType === 'video' ? t('nav.video') : t('nav.audio')}
              </span>
              <button
                className="secondary-button profile-action-btn"
                onClick={() => {
                  handleLoad(profile)
                }}
                title={t('profile.load')}
                aria-label={t('profile.load')}
              >
                <Download size={14} />
              </button>
              <button
                className="secondary-button profile-action-btn"
                onClick={() => {
                  handleDelete(profile.name)
                }}
                title={t('profile.delete')}
                aria-label={t('profile.delete')}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p
          className="text-muted"
          style={{ fontSize: '0.85rem', textAlign: 'center', padding: '16px 0' }}
        >
          {t('profile.no_profiles')}
        </p>
      )}
      {statusMessage && (
        <div className="status-message" style={{ marginTop: '8px' }} role="status">
          {statusMessage}
        </div>
      )}
    </div>
  )
}

const FloatingBar: React.FC<FloatingBarProps> = ({
  onStartCompression,
  compressionDisabled,
  isCompressing,
  jobs,
  onCancelJob,
  onDismissJob,
  currentSettings,
  onApplyProfile,
  onApplyDefaults,
}) => {
  const { t } = useTranslation()
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [progressModalOpen, setProgressModalOpen] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [confirmState, setConfirmState] = useState<ConfirmState>(INITIAL_CONFIRM_STATE)
  const profileModalRef = useRef<HTMLDivElement>(null)
  const progressModalRef = useRef<HTMLDivElement>(null)
  const prevIsCompressingRef = useRef(false)

  const showToast = useCallback((msg: string): void => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    setToastMessage(msg)
    toastTimerRef.current = setTimeout(() => {
      setToastMessage('')
      toastTimerRef.current = null
    }, 3000)
  }, [])

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>
    if (prevIsCompressingRef.current && !isCompressing) {
      timer = setTimeout(() => {
        showToast(t('compress.process_complete'))
      }, 1500)
    }
    prevIsCompressingRef.current = isCompressing
    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [isCompressing, showToast, t])

  const closeProfileModal = useCallback((): void => {
    setProfileModalOpen(false)
  }, [])

  const closeProgressModal = useCallback((): void => {
    setProgressModalOpen(false)
  }, [])

  useClickOutside(profileModalRef, profileModalOpen, closeProfileModal, '[data-profile-trigger]')
  useClickOutside(
    progressModalRef,
    progressModalOpen && !isCompressing,
    closeProgressModal,
    '[data-progress-trigger]',
  )

  const runningJobs = jobs.filter((j) => j.status === 'running' || j.status === 'starting')
  const hasJobs = jobs.length > 0

  const handleStartClick = (): void => {
    setProgressModalOpen(true)
    setProfileModalOpen(false)
    onStartCompression()
  }

  return (
    <>
      <div className="floating-bar" role="toolbar" aria-label={t('compress.start')}>
        <div className="floating-bar-left">
          <button
            className="floating-bar-btn"
            onClick={() => {
              setProfileModalOpen(!profileModalOpen)
              if (!isCompressing) setProgressModalOpen(false)
            }}
            disabled={isCompressing}
            aria-haspopup="dialog"
            aria-expanded={profileModalOpen}
            data-profile-trigger
          >
            <Save size={15} />
            <span>{t('profile.title')}</span>
          </button>

          <button
            className="floating-bar-btn"
            onClick={() => {
              if (isCompressing && progressModalOpen) return
              setProgressModalOpen(!progressModalOpen)
              setProfileModalOpen(false)
            }}
            data-progress-trigger
          >
            {runningJobs.length > 0 ? (
              <Loader2 size={15} className="spin" />
            ) : (
              <span className="floating-bar-btn-dot" />
            )}
            <span>{t('compress.progress')}</span>
            {hasJobs && (
              <span
                className="floating-bar-badge"
                aria-label={`${jobs.length} ${t('compress.progress').toLowerCase()}`}
              >
                {jobs.length}
              </span>
            )}
          </button>
        </div>

        <div className="floating-bar-right">
          <button
            className="primary-button floating-bar-start-btn"
            onClick={handleStartClick}
            disabled={compressionDisabled || isCompressing}
            aria-busy={isCompressing}
          >
            {isCompressing ? <Loader2 className="spin" size={16} /> : <Play size={16} />}
            {t('compress.start')}
          </button>
        </div>
      </div>

      {profileModalOpen && (
        <div className="modal-overlay" onClick={closeProfileModal} role="presentation">
          <div
            className="modal-content"
            ref={profileModalRef}
            onClick={(e) => {
              e.stopPropagation()
            }}
            role="dialog"
            aria-modal="true"
            aria-label={t('profile.title')}
          >
            <div className="modal-header">
              <h3>
                <Save size={16} /> {t('profile.title')}
              </h3>
              <button
                className="panel-close-button"
                onClick={closeProfileModal}
                aria-label={t('common.close')}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <ProfileModalContent
                t={t}
                currentSettings={currentSettings}
                onApplyProfile={onApplyProfile}
                onApplyDefaults={onApplyDefaults}
                onClose={closeProfileModal}
                onNotify={showToast}
                setConfirmState={setConfirmState}
              />
            </div>
          </div>
        </div>
      )}

      {progressModalOpen && (
        <div
          className="modal-overlay"
          onClick={isCompressing ? undefined : closeProgressModal}
          role="presentation"
        >
          <div
            className="modal-content modal-content-progress"
            ref={progressModalRef}
            onClick={(e) => {
              e.stopPropagation()
            }}
            role="dialog"
            aria-modal="true"
            aria-label={t('compress.progress')}
          >
            <div className="modal-header">
              <h3>{t('compress.progress')}</h3>
              {!isCompressing && (
                <button
                  className="panel-close-button"
                  onClick={closeProgressModal}
                  aria-label={t('common.close')}
                >
                  <X size={16} />
                </button>
              )}
            </div>
            <div className="modal-body">
              {hasJobs ? (
                <ProgressPanel
                  jobs={jobs}
                  onCancel={onCancelJob}
                  onDismiss={onDismissJob}
                  embedded
                />
              ) : (
                <div className="progress-empty">
                  <p className="text-muted">{t('compress.no_jobs')}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {toastMessage && (
        <div className="toast-notification toast-success" role="status" aria-live="polite">
          {toastMessage}
        </div>
      )}
      <ConfirmModal
        open={confirmState.open}
        title={confirmState.title}
        message={confirmState.message}
        confirmLabel={confirmState.confirmLabel}
        cancelLabel={t('common.cancel')}
        variant={confirmState.variant}
        onConfirm={confirmState.onConfirm ?? (() => undefined)}
        onCancel={() => {
          setConfirmState(INITIAL_CONFIRM_STATE)
        }}
      />
    </>
  )
}

export default FloatingBar
