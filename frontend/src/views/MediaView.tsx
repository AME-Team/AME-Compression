import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useImperativeHandle,
  useMemo,
} from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Upload, Settings, FileSearch, ChevronDown, X } from 'lucide-react'
import { api } from '../services/api'
import type { MediaProfile } from '../profiles'
import { DEFAULT_SETTINGS } from '../profiles'

const AUDIO_EXTENSIONS = new Set(['mp3', 'wav', 'flac', 'm4a'])

function detectMediaType(filePath: string): 'video' | 'audio' {
  const ext = filePath.split('.').pop()?.toLowerCase() ?? ''
  if (AUDIO_EXTENSIONS.has(ext)) return 'audio'
  return 'video'
}

const AUDIO_BITRATE_OPTIONS = [
  '16',
  '24',
  '32',
  '40',
  '48',
  '64',
  '96',
  '128',
  '160',
  '192',
  '256',
  '320',
]
const FPS_OPTIONS = ['240', '144', '120', '90', '60', '50', '48', '30', '25', '24', '20', '12']
const BITRATE_REGEX = /^\d+$/

interface ComboBoxProps {
  value: string
  onChange: (val: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  disabled?: boolean
  sanitize?: (val: string) => string
}

const ComboBox: React.FC<ComboBoxProps> = ({
  value,
  onChange,
  options,
  placeholder,
  disabled,
  sanitize,
}) => {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        containerRef.current &&
        e.target instanceof Element &&
        !containerRef.current.contains(e.target)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return (): void => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(e) => {
            const sanitized = sanitize ? sanitize(e.target.value) : e.target.value
            onChange(sanitized)
          }}
          onBlur={() => {
            if (sanitize && value !== '' && !/^\d+$/.test(value)) {
              onChange('')
            }
          }}
          style={{ flex: 1, borderRadius: 'var(--border-radius, 0)' }}
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
        />
        <button
          type="button"
          className="secondary-button"
          disabled={disabled}
          onClick={() => {
            setOpen(!open)
          }}
          style={{
            borderRadius: 'var(--border-radius, 0)',
            padding: '0 8px',
            borderLeft: 'none',
            minWidth: '32px',
          }}
          aria-label="Toggle dropdown"
        >
          <ChevronDown size={14} />
        </button>
      </div>
      {open && (
        <ul
          role="listbox"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 1000,
            listStyle: 'none',
            margin: 0,
            padding: 0,
            maxHeight: '200px',
            overflowY: 'auto',
            background: 'var(--card-bg)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--border-radius, 0)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}
        >
          {options.map((opt) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={value === opt.value}
              onClick={(): void => {
                onChange(opt.value)
                setOpen(false)
              }}
              className="combobox-option"
              style={{
                padding: '6px 10px',
                cursor: 'pointer',
                background: value === opt.value ? 'var(--primary-color)' : 'transparent',
                color: value === opt.value ? '#fff' : 'inherit',
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

interface AudioSettingsSectionProps {
  t: TFunction
  volumeMode: string
  setVolumeMode: (val: string) => void
  volumeValue: number
  setVolumeValue: (val: number) => void
  denoiseEnabled: boolean
  setDenoiseEnabled: (val: boolean) => void
  denoiseLevel: number
  setDenoiseLevel: (val: number) => void
}

const AudioSettingsSection: React.FC<AudioSettingsSectionProps> = ({
  t,
  volumeMode,
  setVolumeMode,
  volumeValue,
  setVolumeValue,
  denoiseEnabled,
  setDenoiseEnabled,
  denoiseLevel,
  setDenoiseLevel,
}) => (
  <>
    <div className="sub-section-title">{t('volume.title')}</div>
    <div className="settings-grid">
      <div className="setting-item">
        <label>{t('volume.mode')}</label>
        <select
          value={volumeMode}
          onChange={(e) => {
            setVolumeMode(e.target.value)
          }}
        >
          <option value="disabled">{t('volume.modes.disabled')}</option>
          <option value="auto">{t('volume.modes.auto')}</option>
          <option value="multiplier">{t('volume.modes.multiplier')}</option>
          <option value="db">{t('volume.modes.db')}</option>
        </select>
      </div>
      {(volumeMode === 'multiplier' || volumeMode === 'db') && (
        <div className="setting-item">
          <label>
            {volumeMode === 'multiplier' ? t('volume.multiplier_label') : t('volume.db_label')}:{' '}
            {volumeValue}
            {volumeMode === 'db' ? ' dB' : 'x'}
          </label>
          <input
            type="range"
            min={volumeMode === 'multiplier' ? '0.1' : '-20'}
            max={volumeMode === 'multiplier' ? '5.0' : '20'}
            step={volumeMode === 'multiplier' ? '0.1' : '1'}
            value={volumeValue}
            onChange={(e) => {
              setVolumeValue(parseFloat(e.target.value))
            }}
          />
        </div>
      )}
    </div>

    <div className="sub-section-title">{t('denoise.title')}</div>
    <div className="settings-grid">
      <div className="setting-item">
        <label>
          <input
            type="checkbox"
            checked={denoiseEnabled}
            onChange={(e) => {
              setDenoiseEnabled(e.target.checked)
            }}
          />{' '}
          {t('denoise.enable')}
        </label>
      </div>
      {denoiseEnabled && (
        <div className="setting-item" style={{ gridColumn: 'span 2' }}>
          <label>
            {t('denoise.level')}: {denoiseLevel}
          </label>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <button
              className={`secondary-button ${denoiseLevel === 0.15 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.15)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.light')}
            </button>
            <button
              className={`secondary-button ${denoiseLevel === 0.4 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.4)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.medium')}
            </button>
            <button
              className={`secondary-button ${denoiseLevel === 0.7 ? 'active' : ''}`}
              onClick={() => {
                setDenoiseLevel(0.7)
              }}
              style={{ flex: 1, padding: '4px' }}
            >
              {t('denoise.presets.strong')}
            </button>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={denoiseLevel}
            onChange={(e) => {
              setDenoiseLevel(parseFloat(e.target.value))
            }}
          />
        </div>
      )}
    </div>
  </>
)

export interface MediaViewHandle {
  startCompression: () => Promise<void>
  getCurrentSettings: () => Omit<MediaProfile, 'name'>
  applyProfile: (settings: Omit<MediaProfile, 'name'>) => void
  applyDefaults: () => void
  getInputPaths: () => string[]
  getLoading: () => boolean
}

export interface MediaViewProps {
  onStateChange?: (state: {
    inputPaths: string[]
    loading: boolean
    settings: Omit<MediaProfile, 'name'>
  }) => void
}

const MediaView = React.forwardRef<MediaViewHandle, MediaViewProps>(({ onStateChange }, ref) => {
  const { t } = useTranslation()
  const [inputPaths, setInputPaths] = useState<string[]>([])
  const [manualInput, setManualInput] = useState('')

  // Video settings
  const [crf, setCrf] = useState(25)
  const [preset, setPreset] = useState(6)
  const [maxResolution, setMaxResolution] = useState('original')
  const [customWidth, setCustomWidth] = useState('')
  const [customHeight, setCustomHeight] = useState('')
  const [maxFps, setMaxFps] = useState('unlimited')
  const [videoAudioBitrate, setVideoAudioBitrate] = useState('192')
  const [audioEnabled, setAudioEnabled] = useState(true)

  // Audio settings
  const [audioBitrate, setAudioBitrate] = useState('192')
  const [keepMetadata, setKeepMetadata] = useState(true)

  // Common settings
  const [volumeMode, setVolumeMode] = useState('disabled')
  const [volumeValue, setVolumeValue] = useState(0)
  const [denoiseEnabled, setDenoiseEnabled] = useState(false)
  const [denoiseLevel, setDenoiseLevel] = useState(0.15)

  const [loading, setLoading] = useState(false)
  const [failedFiles, setFailedFiles] = useState<string[]>([])
  const [mediaType, setMediaType] = useState<'video' | 'audio'>('video')
  const [isDragging, setIsDragging] = useState(false)

  const currentSettings: Omit<MediaProfile, 'name'> = useMemo(
    () => ({
      mediaType,
      crf,
      preset,
      maxResolution,
      customWidth,
      customHeight,
      maxFps,
      videoAudioBitrate,
      audioEnabled,
      audioBitrate,
      keepMetadata,
      volumeMode,
      volumeValue,
      denoiseEnabled,
      denoiseLevel,
    }),
    [
      mediaType,
      crf,
      preset,
      maxResolution,
      customWidth,
      customHeight,
      maxFps,
      videoAudioBitrate,
      audioEnabled,
      audioBitrate,
      keepMetadata,
      volumeMode,
      volumeValue,
      denoiseEnabled,
      denoiseLevel,
    ],
  )

  const applyProfile = useCallback((settings: Omit<MediaProfile, 'name'>): void => {
    setMediaType(settings.mediaType)
    setCrf(settings.crf)
    setPreset(settings.preset)
    setMaxResolution(settings.maxResolution)
    setCustomWidth(settings.customWidth)
    setCustomHeight(settings.customHeight)
    setMaxFps(settings.maxFps)
    setVideoAudioBitrate(settings.videoAudioBitrate)
    setAudioEnabled(settings.audioEnabled)
    setAudioBitrate(settings.audioBitrate)
    setKeepMetadata(settings.keepMetadata)
    setVolumeMode(settings.volumeMode)
    setVolumeValue(settings.volumeValue)
    setDenoiseEnabled(settings.denoiseEnabled)
    setDenoiseLevel(settings.denoiseLevel)
  }, [])

  const applyDefaults = useCallback((): void => {
    applyProfile(DEFAULT_SETTINGS)
  }, [applyProfile])

  const handleSelectFiles = async (): Promise<void> => {
    if (!window.electronAPI) return
    const paths = await window.electronAPI.selectFiles()
    if (paths && paths.length > 0) {
      setInputPaths((prev) => {
        const newPaths = paths.filter((p) => !prev.includes(p))
        return [...prev, ...newPaths]
      })
    }
  }

  const handleDragOver = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'copy'
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    const newPaths: string[] = []
    for (const file of files) {
      const filePath = window.electronAPI?.getPathForFile?.(file) ?? file.path ?? ''
      if (filePath && !newPaths.includes(filePath)) {
        newPaths.push(filePath)
      }
    }
    if (newPaths.length > 0) {
      setInputPaths((prev) => {
        const filtered = newPaths.filter((p) => !prev.includes(p))
        return [...prev, ...filtered]
      })
    }
  }

  const addManualPath = (): void => {
    const trimmed = manualInput.trim()
    if (trimmed && !inputPaths.includes(trimmed)) {
      setInputPaths((prev) => [...prev, trimmed])
      setManualInput('')
    }
  }

  const removeFile = (index: number): void => {
    setInputPaths((prev) => prev.filter((_, i) => i !== index))
  }

  const clearFiles = (): void => {
    setInputPaths([])
  }

  useEffect(() => {
    const preventDefault = (e: DragEvent): void => {
      e.preventDefault()
    }
    window.addEventListener('dragover', preventDefault)
    window.addEventListener('drop', preventDefault)
    return () => {
      window.removeEventListener('dragover', preventDefault)
      window.removeEventListener('drop', preventDefault)
    }
  }, [])

  const startCompression = async (): Promise<void> => {
    setLoading(true)
    setFailedFiles([])

    let volumeGain = null
    if (volumeMode === 'auto') volumeGain = 'auto'
    else if (volumeMode === 'multiplier') volumeGain = `${volumeValue}`
    else if (volumeMode === 'db') volumeGain = `${volumeValue}dB`

    let resolution = maxResolution
    if (maxResolution === 'custom' && customWidth && customHeight) {
      resolution = `${customWidth}x${customHeight}`
    }

    const resolvedVideoAudioBitrate = BITRATE_REGEX.test(videoAudioBitrate)
      ? videoAudioBitrate + 'k'
      : '192k'
    const resolvedAudioBitrate = BITRATE_REGEX.test(audioBitrate) ? audioBitrate + 'k' : '192k'

    const failed: string[] = []
    try {
      for (const inputPath of inputPaths) {
        const detectedType = detectMediaType(inputPath)
        if (detectedType === 'video') {
          await api
            .post<{ task_id: string }>('/jobs/video', {
              input_path: inputPath,
              crf,
              preset,
              audio_bitrate: resolvedVideoAudioBitrate,
              audio_enabled: audioEnabled,
              resolution: resolution === 'original' ? null : resolution,
              max_fps:
                maxFps === 'unlimited'
                  ? null
                  : Number.isFinite(parseInt(maxFps, 10))
                    ? parseInt(maxFps, 10)
                    : null,
              volume_gain_db: volumeGain,
              denoise_level: denoiseEnabled ? denoiseLevel : null,
            })
            .catch((error) => {
              console.error(`Failed to start compression for ${inputPath}`, error)
              failed.push(inputPath)
            })
        } else {
          await api
            .post<{ task_id: string }>('/jobs/audio', {
              input_path: inputPath,
              bitrate: resolvedAudioBitrate,
              keep_metadata: keepMetadata,
              volume_gain_db: volumeGain,
              denoise_level: denoiseEnabled ? denoiseLevel : null,
            })
            .catch((error) => {
              console.error(`Failed to start compression for ${inputPath}`, error)
              failed.push(inputPath)
            })
        }
      }
    } finally {
      if (failed.length > 0) setFailedFiles(failed)
      setLoading(false)
    }
  }

  useImperativeHandle(ref, () => ({
    startCompression,
    getCurrentSettings: () => currentSettings,
    applyProfile,
    applyDefaults,
    getInputPaths: () => inputPaths,
    getLoading: () => loading,
  }))

  useEffect(() => {
    onStateChange?.({ inputPaths, loading, settings: currentSettings })
  }, [inputPaths, loading, currentSettings, onStateChange])

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.video_audio')}</h1>
        <p>
          {t('video_settings.title')} / {t('audio_settings.title')}
        </p>
      </header>

      <section
        className={`card drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <h2>
          <Upload size={18} /> {t('file.select_multiple')}
        </h2>
        <div className="input-with-button">
          <input
            type="text"
            placeholder={t('file.browse_hint')}
            value={manualInput}
            onChange={(e) => {
              setManualInput(e.target.value)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') addManualPath()
            }}
          />
          <button className="secondary-button" onClick={() => void handleSelectFiles()}>
            <FileSearch size={18} />
          </button>
        </div>
        {inputPaths.length > 0 && (
          <div className="file-list">
            {inputPaths.map((filePath, index) => (
              <div key={filePath} className="file-list-item">
                <span className="file-list-path" title={filePath}>
                  {filePath.split(/[\\/]/).pop()}
                </span>
                <button
                  className="file-remove-button"
                  onClick={() => {
                    removeFile(index)
                  }}
                  aria-label={t('file.remove')}
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="file-list-actions">
          {inputPaths.length > 0 ? (
            <>
              <span className="file-count">
                {t('file.selected_count', { count: inputPaths.length })}
              </span>
              <button
                className="secondary-button"
                onClick={clearFiles}
                style={{ fontSize: '0.8rem', padding: '4px 8px' }}
              >
                {t('file.clear_all')}
              </button>
            </>
          ) : (
            <span className="file-count text-muted">{t('file.no_files')}</span>
          )}
        </div>
        {failedFiles.length > 0 && (
          <div
            style={{
              marginTop: '12px',
              padding: '8px 12px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '6px',
            }}
          >
            <p
              style={{ margin: '0 0 4px', color: '#dc2626', fontWeight: 600, fontSize: '0.85rem' }}
            >
              {t('file.failed_count', { count: failedFiles.length })}
            </p>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#991b1b', fontSize: '0.8rem' }}>
              {failedFiles.map((f) => (
                <li key={f}>{f.split(/[\\/]/).pop()}</li>
              ))}
            </ul>
          </div>
        )}
        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'inline-block', marginRight: '16px' }}>
            <input
              type="radio"
              checked={mediaType === 'video'}
              onChange={() => {
                setMediaType('video')
              }}
            />{' '}
            {t('nav.video')}
          </label>
          <label style={{ display: 'inline-block' }}>
            <input
              type="radio"
              checked={mediaType === 'audio'}
              onChange={() => {
                setMediaType('audio')
              }}
            />{' '}
            {t('nav.audio')}
          </label>
        </div>
      </section>

      <section className="card">
        <h2>
          <Settings size={18} />{' '}
          {mediaType === 'video' ? t('video_settings.title') : t('audio_settings.title')}
        </h2>

        {mediaType === 'video' ? (
          <>
            <div className="section-title">{t('video_settings.video_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>
                  {t('video_settings.crf')}: {crf}
                </label>
                <input
                  type="range"
                  min="0"
                  max="63"
                  value={crf}
                  onChange={(e) => {
                    setCrf(parseInt(e.target.value))
                  }}
                />
                <small>{t('video_settings.crf_range')}</small>
              </div>
              <div className="setting-item">
                <label>
                  {t('video_settings.preset')}: {preset}
                </label>
                <input
                  type="range"
                  min="0"
                  max="13"
                  value={preset}
                  onChange={(e) => {
                    setPreset(parseInt(e.target.value))
                  }}
                />
                <small>{t('video_settings.preset_range')}</small>
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_resolution')}</label>
                <select
                  value={maxResolution}
                  onChange={(e) => {
                    setMaxResolution(e.target.value)
                  }}
                >
                  <option value="original">{t('video_settings.resolution.original')}</option>
                  <option value="3840x2160">{t('video_settings.resolution.4k')}</option>
                  <option value="1920x1080">{t('video_settings.resolution.1080p')}</option>
                  <option value="1280x720">{t('video_settings.resolution.720p')}</option>
                  <option value="854x480">{t('video_settings.resolution.480p')}</option>
                  <option value="custom">{t('video_settings.resolution.custom')}</option>
                </select>
                {maxResolution === 'custom' && (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    <input
                      type="number"
                      placeholder="W"
                      value={customWidth}
                      onChange={(e) => {
                        setCustomWidth(e.target.value)
                      }}
                    />
                    <input
                      type="number"
                      placeholder="H"
                      value={customHeight}
                      onChange={(e) => {
                        setCustomHeight(e.target.value)
                      }}
                    />
                  </div>
                )}
              </div>
              <div className="setting-item">
                <label>{t('video_settings.max_fps')}</label>
                <ComboBox
                  value={maxFps === 'unlimited' ? '' : maxFps}
                  onChange={(val) => {
                    setMaxFps(val || 'unlimited')
                  }}
                  sanitize={(val) => val.replace(/[^\d]/g, '')}
                  placeholder={t('video_settings.fps_options.unlimited')}
                  options={FPS_OPTIONS.map((fps) => ({
                    value: fps,
                    label: t('video_settings.fps_options.' + fps, fps + ' FPS'),
                  }))}
                />
              </div>
            </div>

            <div className="section-title">{t('video_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('video_settings.audio_bitrate')}</label>
                <ComboBox
                  value={videoAudioBitrate}
                  onChange={(val) => {
                    setVideoAudioBitrate(BITRATE_REGEX.test(val) ? val : '192')
                  }}
                  placeholder="e.g. 192"
                  disabled={!audioEnabled}
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={!audioEnabled}
                    onChange={(e) => {
                      setAudioEnabled(!e.target.checked)
                    }}
                  />{' '}
                  {t('video_settings.disable_audio')}
                </label>
              </div>
            </div>
            <AudioSettingsSection
              t={t}
              volumeMode={volumeMode}
              setVolumeMode={setVolumeMode}
              volumeValue={volumeValue}
              setVolumeValue={setVolumeValue}
              denoiseEnabled={denoiseEnabled}
              setDenoiseEnabled={setDenoiseEnabled}
              denoiseLevel={denoiseLevel}
              setDenoiseLevel={setDenoiseLevel}
            />
          </>
        ) : (
          <>
            <div className="section-title">{t('audio_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('audio_settings.bitrate')}</label>
                <ComboBox
                  value={audioBitrate}
                  onChange={(val) => {
                    setAudioBitrate(BITRATE_REGEX.test(val) ? val : '192')
                  }}
                  placeholder="e.g. 192"
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={keepMetadata}
                    onChange={(e) => {
                      setKeepMetadata(e.target.checked)
                    }}
                  />{' '}
                  {t('audio_settings.keep_metadata')}
                </label>
              </div>
            </div>
            <AudioSettingsSection
              t={t}
              volumeMode={volumeMode}
              setVolumeMode={setVolumeMode}
              volumeValue={volumeValue}
              setVolumeValue={setVolumeValue}
              denoiseEnabled={denoiseEnabled}
              setDenoiseEnabled={setDenoiseEnabled}
              denoiseLevel={denoiseLevel}
              setDenoiseLevel={setDenoiseLevel}
            />
          </>
        )}
      </section>
    </div>
  )
})

MediaView.displayName = 'MediaView'

export default MediaView
