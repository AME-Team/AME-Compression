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
import { Upload, Settings, FileSearch, X, Sparkles } from 'lucide-react'
import { api } from '../services/api'
import type { MediaProfile } from '../profiles'
import { DEFAULT_SETTINGS } from '../profiles'
import type { QualityAnalysisResult, BatchAnalysisItem, AnalysisMode } from '../types'
import Dropdown from '../components/Dropdown'

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
  disabled?: boolean
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
  disabled = false,
}) => {
  const isLight = denoiseLevel >= 0.0 && denoiseLevel < 0.3
  const isMedium = denoiseLevel >= 0.3 && denoiseLevel < 0.6
  const isStrong = denoiseLevel >= 0.6 && denoiseLevel <= 1.0
  const activePresetLabel = isLight
    ? t('denoise.presets.light')
    : isMedium
      ? t('denoise.presets.medium')
      : isStrong
        ? t('denoise.presets.strong')
        : ''

  return (
    <>
      <div className={`sub-section-title ${disabled ? 'disabled-label' : ''}`}>
        {t('volume.title')}
      </div>
      <div className="settings-grid">
        <div className="setting-item">
          <label htmlFor="volume-mode" className={disabled ? 'disabled-label' : ''}>
            {t('volume.mode')}
          </label>
          <Dropdown
            id="volume-mode"
            value={volumeMode}
            onChange={(val) => {
              setVolumeMode(val)
              if (val === 'multiplier') {
                setVolumeValue(1.0)
              } else {
                setVolumeValue(0)
              }
            }}
            disabled={disabled}
            ariaLabel={t('volume.mode')}
            options={[
              { value: 'disabled', label: t('volume.modes.disabled') },
              { value: 'auto', label: t('volume.modes.auto') },
              { value: 'multiplier', label: t('volume.modes.multiplier') },
              { value: 'db', label: t('volume.modes.db') },
            ]}
          />
        </div>
        {(volumeMode === 'multiplier' || volumeMode === 'db') && (
          <div className="setting-item">
            <label htmlFor="volume-slider" className={disabled ? 'disabled-label' : ''}>
              {volumeMode === 'multiplier' ? t('volume.multiplier_label') : t('volume.db_label')}:{' '}
              {volumeValue}
              {volumeMode === 'db' ? ' dB' : 'x'}
            </label>
            <input
              id="volume-slider"
              type="range"
              min={volumeMode === 'multiplier' ? '0.1' : '-20'}
              max={volumeMode === 'multiplier' ? '5.0' : '20'}
              step={volumeMode === 'multiplier' ? '0.1' : '1'}
              value={volumeValue}
              disabled={disabled}
              onChange={(e) => {
                setVolumeValue(parseFloat(e.target.value))
              }}
              aria-label={`${volumeMode === 'multiplier' ? t('volume.multiplier_label') : t('volume.db_label')}: ${volumeValue}`}
            />
          </div>
        )}
      </div>

      <div className={`sub-section-title ${disabled ? 'disabled-label' : ''}`}>
        {t('denoise.title')}
      </div>
      <div className="settings-grid">
        <div className="setting-item">
          <label htmlFor="denoise-toggle" className={disabled ? 'disabled-label' : ''}>
            <input
              id="denoise-toggle"
              type="checkbox"
              checked={denoiseEnabled}
              disabled={disabled}
              onChange={(e) => {
                setDenoiseEnabled(e.target.checked)
              }}
            />{' '}
            {t('denoise.enable')}
          </label>
        </div>
        {denoiseEnabled && (
          <div className="setting-item span-2">
            <label htmlFor="denoise-slider" className={disabled ? 'disabled-label' : ''}>
              {t('denoise.level')}: {denoiseLevel} ({activePresetLabel})
            </label>
            <div className="preset-row">
              <button
                className={`secondary-button preset-button ${isLight ? 'active' : ''}`}
                onClick={() => {
                  setDenoiseLevel(0.15)
                }}
                aria-pressed={isLight}
                disabled={disabled}
              >
                {t('denoise.presets.light')}
              </button>
              <button
                className={`secondary-button preset-button ${isMedium ? 'active' : ''}`}
                onClick={() => {
                  setDenoiseLevel(0.4)
                }}
                aria-pressed={isMedium}
                disabled={disabled}
              >
                {t('denoise.presets.medium')}
              </button>
              <button
                className={`secondary-button preset-button ${isStrong ? 'active' : ''}`}
                onClick={() => {
                  setDenoiseLevel(0.7)
                }}
                aria-pressed={isStrong}
                disabled={disabled}
              >
                {t('denoise.presets.strong')}
              </button>
            </div>
            <input
              id="denoise-slider"
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={denoiseLevel}
              disabled={disabled}
              onChange={(e) => {
                setDenoiseLevel(parseFloat(e.target.value))
              }}
              aria-label={`${t('denoise.level')}: ${denoiseLevel}`}
            />
          </div>
        )}
      </div>
    </>
  )
}

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

  const [crf, setCrf] = useState(25)
  const [preset, setPreset] = useState(6)
  const [maxResolution, setMaxResolution] = useState('original')
  const [customWidth, setCustomWidth] = useState('')
  const [customHeight, setCustomHeight] = useState('')
  const [maxFps, setMaxFps] = useState('unlimited')
  const [videoAudioBitrate, setVideoAudioBitrate] = useState('192')
  const [audioEnabled, setAudioEnabled] = useState(true)

  const [audioBitrate, setAudioBitrate] = useState('192')
  const [keepMetadata, setKeepMetadata] = useState(true)

  const [volumeMode, setVolumeMode] = useState('disabled')
  const [volumeValue, setVolumeValue] = useState(0)
  const [denoiseEnabled, setDenoiseEnabled] = useState(false)
  const [denoiseLevel, setDenoiseLevel] = useState(0.15)

  const [loading, setLoading] = useState(false)
  const [failedFiles, setFailedFiles] = useState<string[]>([])
  const [mediaType, setMediaType] = useState<'video' | 'audio'>('video')
  const [isDragging, setIsDragging] = useState(false)
  const [dropSuccess, setDropSuccess] = useState(false)
  const dropSuccessTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const [analyzingQuality, setAnalyzingQuality] = useState(false)
  const [qualityResult, setQualityResult] = useState<QualityAnalysisResult | null>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('none')
  const [batchAnalysisResults, setBatchAnalysisResults] = useState<BatchAnalysisItem[]>([])
  const [batchAnalyzing, setBatchAnalyzing] = useState(false)
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 })

  const isAnalysisActive = analysisMode !== 'none'
  const disableCrf = isAnalysisActive && (analysisMode === 'all' || analysisMode === 'video')
  const disableAudioSettings =
    isAnalysisActive && (analysisMode === 'all' || analysisMode === 'audio')

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
      setDropSuccess(true)
      if (dropSuccessTimeoutRef.current) {
        clearTimeout(dropSuccessTimeoutRef.current)
      }
      dropSuccessTimeoutRef.current = setTimeout(() => {
        setDropSuccess(false)
      }, 600)
    }
  }

  const handleKeyboardFileSelect = (): void => {
    void handleSelectFiles()
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

  useEffect(() => {
    return () => {
      if (dropSuccessTimeoutRef.current) {
        clearTimeout(dropSuccessTimeoutRef.current)
      }
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

    const getPerFileCrf = (inputPath: string): number => {
      if (!isAnalysisActive) return crf
      const analysis = batchAnalysisResults.find((r) => r.path === inputPath)
      if (analysis?.result.status === 'success' && analysis.result.media_type === 'video') {
        return analysis.result.recommended_crf ?? crf
      }
      return crf
    }

    const getPerFileDenoise = (inputPath: string): { enabled: boolean; level: number } => {
      if (!isAnalysisActive) return { enabled: denoiseEnabled, level: denoiseLevel }
      const analysis = batchAnalysisResults.find((r) => r.path === inputPath)
      if (analysis?.result.status === 'success' && analysis.result.media_type === 'video') {
        return {
          enabled: analysis.result.recommend_denoise ?? denoiseEnabled,
          level: analysis.result.denoise_level ?? denoiseLevel,
        }
      }
      return { enabled: denoiseEnabled, level: denoiseLevel }
    }

    const getPerFileAudioBitrate = (inputPath: string): string => {
      if (!isAnalysisActive) return resolvedAudioBitrate
      const analysis = batchAnalysisResults.find((r) => r.path === inputPath)
      if (analysis?.result.status === 'success' && analysis.result.media_type === 'audio') {
        const recommended = analysis.result.recommended_bitrate
        if (recommended) return `${recommended}k`
      }
      return resolvedAudioBitrate
    }

    const failed: string[] = []
    try {
      for (const inputPath of inputPaths) {
        const detectedType = detectMediaType(inputPath)
        const fileCrf = getPerFileCrf(inputPath)
        const fileDenoise = getPerFileDenoise(inputPath)

        if (detectedType === 'video') {
          await api
            .post<{ task_id: string }>('/jobs/video', {
              input_path: inputPath,
              crf: fileCrf,
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
              denoise_level: fileDenoise.enabled ? fileDenoise.level : null,
            })
            .catch((error) => {
              console.error(`Failed to start compression for ${inputPath}`, error)
              failed.push(inputPath)
            })
        } else {
          const fileAudioBitrate = getPerFileAudioBitrate(inputPath)
          await api
            .post<{ task_id: string }>('/jobs/audio', {
              input_path: inputPath,
              bitrate: fileAudioBitrate,
              keep_metadata: keepMetadata,
              volume_gain_db: volumeGain,
              denoise_level: fileDenoise.enabled ? fileDenoise.level : null,
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

  const handleAnalyzeQuality = async (): Promise<void> => {
    if (inputPaths.length === 0) return
    const firstFile = inputPaths[0]
    if (!firstFile) return

    setAnalyzingQuality(true)
    setQualityResult(null)
    try {
      const response = await api.post<QualityAnalysisResult>('/media/analyze-settings', {
        path: firstFile,
      })
      setQualityResult(response.data)
    } catch (error) {
      console.error('Quality analysis failed', error)
    } finally {
      setAnalyzingQuality(false)
    }
  }

  const applyQualitySettings = (): void => {
    if (qualityResult?.status !== 'success') return
    const firstFile = inputPaths[0]
    if (!firstFile) return
    const mediaType = detectMediaType(firstFile)

    if (mediaType === 'audio') {
      if (qualityResult.recommended_bitrate) {
        setAudioBitrate(qualityResult.recommended_bitrate.toString())
      }
    } else {
      if (qualityResult.recommended_crf !== null) {
        setCrf(qualityResult.recommended_crf)
      }
    }

    if (qualityResult.recommend_denoise && qualityResult.denoise_level !== null) {
      setDenoiseEnabled(true)
      setDenoiseLevel(qualityResult.denoise_level)
    } else {
      setDenoiseEnabled(false)
    }

    if (
      qualityResult.recommended_volume_gain !== undefined &&
      qualityResult.recommended_volume_gain !== null
    ) {
      setVolumeMode('db')
      setVolumeValue(Math.round(qualityResult.recommended_volume_gain * 10) / 10)
    }

    setQualityResult(null)
  }

  const handleBatchAnalyze = async (): Promise<void> => {
    if (inputPaths.length === 0) return
    let targetPaths: string[]
    if (analysisMode === 'video') {
      targetPaths = inputPaths.filter((p) => detectMediaType(p) === 'video')
    } else if (analysisMode === 'audio') {
      targetPaths = inputPaths.filter((p) => detectMediaType(p) === 'audio')
    } else {
      targetPaths = [...inputPaths]
    }
    if (targetPaths.length === 0) return

    setBatchAnalyzing(true)
    setBatchAnalysisResults([])
    setBatchProgress({ current: 0, total: targetPaths.length })
    try {
      const response = await api.post<QualityAnalysisResult[]>('/media/batch-analyze-settings', {
        paths: targetPaths,
        mode: analysisMode,
      })
      setBatchAnalysisResults(
        response.data.map((item) => ({
          path: item.path ?? '',
          result: item,
        })),
      )
      setBatchProgress({ current: targetPaths.length, total: targetPaths.length })
    } catch (error) {
      console.error('Batch analysis failed', error)
    } finally {
      setBatchAnalyzing(false)
    }
  }

  const clearBatchAnalysis = (): void => {
    setBatchAnalysisResults([])
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

  useEffect(() => {
    if (analysisMode === 'none') {
      setBatchAnalysisResults([])
    }
  }, [analysisMode])

  useEffect(() => {
    setBatchAnalysisResults((prev) => prev.filter((r) => inputPaths.includes(r.path)))
  }, [inputPaths])

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.video_audio')}</h1>
        <p>
          {t('video_settings.title')} / {t('audio_settings.title')}
        </p>
      </header>

      <section
        className={`card drop-zone ${isDragging ? 'dragging' : ''} ${dropSuccess ? 'drop-success' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-label={t('a11y.drop_zone_label')}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleKeyboardFileSelect()
          }
        }}
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
            aria-label={t('file.browse_hint')}
          />
          <button
            className="secondary-button"
            onClick={() => void handleSelectFiles()}
            aria-label={t('file.select')}
          >
            <FileSearch size={18} />
          </button>
        </div>
        {inputPaths.length > 0 && (
          <div
            className="file-list"
            role="list"
            aria-label={t('file.selected_count', { count: inputPaths.length })}
          >
            {inputPaths.map((filePath, index) => {
              const analysis = batchAnalysisResults.find((r) => r.path === filePath)
              return (
                <div key={filePath} className="file-list-item" role="listitem">
                  <span className="file-list-path" title={filePath}>
                    {filePath.split(/[\\/]/).pop()}
                  </span>
                  {analysis?.result.status === 'success' && (
                    <span className="file-analysis-badge" title={analysis.result.reason}>
                      {analysis.result.media_type === 'audio'
                        ? t('quality_analysis.bitrate_label', {
                            value: analysis.result.recommended_bitrate,
                          })
                        : t('quality_analysis.crf_label', {
                            value: analysis.result.recommended_crf,
                          })}
                    </span>
                  )}
                  <button
                    className="file-remove-button"
                    onClick={() => {
                      removeFile(index)
                    }}
                    aria-label={`${t('file.remove')}: ${filePath.split(/[\\/]/).pop()}`}
                  >
                    <X size={14} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
        <div className="file-list-actions">
          {inputPaths.length > 0 ? (
            <>
              <span className="file-count">
                {t('file.selected_count', { count: inputPaths.length })}
              </span>
              <button className="secondary-button btn-mini" onClick={clearFiles}>
                {t('file.clear_all')}
              </button>
            </>
          ) : (
            <span className="file-count text-muted">{t('file.no_files')}</span>
          )}
        </div>
        {failedFiles.length > 0 && (
          <div className="error-panel" role="alert">
            <p className="error-panel-title">
              {t('file.failed_count', { count: failedFiles.length })}
            </p>
            <ul className="error-panel-list">
              {failedFiles.map((f) => (
                <li key={f}>{f.split(/[\\/]/).pop()}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="media-type-group" role="radiogroup" aria-label={t('nav.video_audio')}>
          <label className="media-type-radio">
            <input
              type="radio"
              name="media-type"
              checked={mediaType === 'video'}
              onChange={() => {
                setMediaType('video')
              }}
            />{' '}
            {t('nav.video')}
          </label>
          <label className="media-type-radio">
            <input
              type="radio"
              name="media-type"
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
            <div className="batch-optimize-header">
              <label htmlFor="analysis-mode" className="batch-optimize-toggle-label">
                {t('quality_analysis.mode_label')}
              </label>
              <Dropdown
                id="analysis-mode"
                value={analysisMode}
                onChange={(val) => {
                  const mode = val
                  if (mode === 'none' || mode === 'all' || mode === 'video' || mode === 'audio') {
                    setAnalysisMode(mode)
                  }
                }}
                ariaLabel={t('quality_analysis.mode_label')}
                options={[
                  { value: 'none', label: t('quality_analysis.mode_none') },
                  { value: 'all', label: t('quality_analysis.mode_all') },
                  { value: 'video', label: t('quality_analysis.mode_video') },
                  { value: 'audio', label: t('quality_analysis.mode_audio') },
                ]}
              />
              {isAnalysisActive && (
                <small className="batch-optimize-hint">
                  {analysisMode === 'all'
                    ? t('quality_analysis.mode_all_description')
                    : analysisMode === 'video'
                      ? t('quality_analysis.mode_video_description')
                      : t('quality_analysis.mode_audio_description')}
                </small>
              )}
            </div>
            <div className="action-row">
              {isAnalysisActive ? (
                <>
                  <button
                    className="secondary-button button-with-icon"
                    disabled={batchAnalyzing || inputPaths.length === 0}
                    onClick={() => void handleBatchAnalyze()}
                    aria-label={t('quality_analysis.batch_analyze')}
                  >
                    <Sparkles size={14} />
                    {batchAnalyzing
                      ? t('quality_analysis.batch_analyzing', {
                          current: batchProgress.current,
                          total: batchProgress.total,
                        })
                      : t('quality_analysis.batch_analyze')}
                  </button>
                  {batchAnalysisResults.length > 0 && (
                    <button
                      className="secondary-button button-with-icon"
                      onClick={clearBatchAnalysis}
                    >
                      {t('file.clear_all')}
                    </button>
                  )}
                </>
              ) : (
                <button
                  className="secondary-button button-with-icon"
                  disabled={analyzingQuality || inputPaths.length === 0}
                  onClick={() => void handleAnalyzeQuality()}
                  aria-label={t('quality_analysis.analyze')}
                >
                  <Sparkles size={14} />
                  {analyzingQuality
                    ? t('quality_analysis.analyzing')
                    : t('quality_analysis.analyze')}
                </button>
              )}
            </div>
            {isAnalysisActive && batchAnalysisResults.length > 0 && (
              <div className="batch-analysis-summary" role="status">
                <span>
                  {batchAnalysisResults.every((r) => r.result.status === 'success')
                    ? t('quality_analysis.batch_complete', {
                        count: batchAnalysisResults.length,
                      })
                    : t('quality_analysis.batch_partial', {
                        success: batchAnalysisResults.filter((r) => r.result.status === 'success')
                          .length,
                        failed: batchAnalysisResults.filter((r) => r.result.status === 'error')
                          .length,
                      })}
                </span>
              </div>
            )}
            {!isAnalysisActive && qualityResult && (
              <div
                className={`analysis-result ${qualityResult.status === 'error' ? 'error' : 'success'}`}
                role="alert"
              >
                <div className="analysis-result-title">{t('quality_analysis.result_title')}</div>
                <div className="analysis-result-grid">
                  <div>
                    <strong>{t('quality_analysis.recommended_crf')}:</strong>{' '}
                    {qualityResult.recommended_crf}
                  </div>
                  <div>
                    <strong>{t('quality_analysis.bpp')}:</strong> {qualityResult.bpp}
                  </div>
                  <div>
                    <strong>{t('quality_analysis.denoise_recommended')}:</strong>{' '}
                    {qualityResult.recommend_denoise
                      ? t('quality_analysis.yes')
                      : t('quality_analysis.no')}
                  </div>
                </div>
                <p className="analysis-result-reason">{qualityResult.reason}</p>
                {qualityResult.status === 'success' && (
                  <button className="primary-button btn-compact" onClick={applyQualitySettings}>
                    {t('quality_analysis.apply_settings')}
                  </button>
                )}
              </div>
            )}
            <div className="settings-grid">
              <div className="setting-item">
                <label htmlFor="crf-slider">
                  {t('video_settings.crf')}: {crf}
                </label>
                <input
                  id="crf-slider"
                  type="range"
                  min="0"
                  max="63"
                  value={crf}
                  disabled={disableCrf}
                  onChange={(e) => {
                    setCrf(parseInt(e.target.value))
                  }}
                  aria-label={`${t('video_settings.crf')}: ${crf}`}
                />
                <small>{t('video_settings.crf_range')}</small>
              </div>
              <div className="setting-item">
                <label htmlFor="preset-slider">
                  {t('video_settings.preset')}: {preset}
                </label>
                <input
                  id="preset-slider"
                  type="range"
                  min="0"
                  max="13"
                  value={preset}
                  onChange={(e) => {
                    setPreset(parseInt(e.target.value))
                  }}
                  aria-label={`${t('video_settings.preset')}: ${preset}`}
                />
                <small>{t('video_settings.preset_range')}</small>
              </div>
              <div className="setting-item">
                <label htmlFor="max-resolution">{t('video_settings.max_resolution')}</label>
                <Dropdown
                  id="max-resolution"
                  value={maxResolution}
                  onChange={(val) => {
                    setMaxResolution(val)
                  }}
                  ariaLabel={t('video_settings.max_resolution')}
                  options={[
                    { value: 'original', label: t('video_settings.resolution.original') },
                    { value: '3840x2160', label: t('video_settings.resolution.4k') },
                    { value: '1920x1080', label: t('video_settings.resolution.1080p') },
                    { value: '1280x720', label: t('video_settings.resolution.720p') },
                    { value: '854x480', label: t('video_settings.resolution.480p') },
                    { value: 'custom', label: t('video_settings.resolution.custom') },
                  ]}
                />
                {maxResolution === 'custom' && (
                  <div className="resolution-row">
                    <input
                      type="number"
                      placeholder={t('video_settings.custom_width_placeholder')}
                      value={customWidth}
                      onChange={(e) => {
                        setCustomWidth(e.target.value)
                      }}
                      aria-label={t('video_settings.custom_width')}
                    />
                    <input
                      type="number"
                      placeholder={t('video_settings.custom_height_placeholder')}
                      value={customHeight}
                      onChange={(e) => {
                        setCustomHeight(e.target.value)
                      }}
                      aria-label={t('video_settings.custom_height')}
                    />
                  </div>
                )}
              </div>
              <div className="setting-item">
                <label htmlFor="max-fps">{t('video_settings.max_fps')}</label>
                <Dropdown
                  editable
                  value={maxFps === 'unlimited' ? '' : maxFps}
                  onChange={(val) => {
                    setMaxFps(val || 'unlimited')
                  }}
                  sanitize={(val) => val.replace(/[^\d]/g, '')}
                  validate={(val) => val === '' || /^\d+$/.test(val)}
                  fallbackValue=""
                  placeholder={t('video_settings.fps_options.unlimited')}
                  ariaLabel={t('video_settings.max_fps')}
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
                <label htmlFor="video-audio-bitrate">{t('video_settings.audio_bitrate')}</label>
                <Dropdown
                  editable
                  value={videoAudioBitrate}
                  onChange={setVideoAudioBitrate}
                  placeholder={t('video_settings.bitrate_placeholder')}
                  disabled={!audioEnabled}
                  ariaLabel={t('video_settings.audio_bitrate')}
                  validate={BITRATE_REGEX.test.bind(BITRATE_REGEX)}
                  fallbackValue="192"
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label htmlFor="disable-audio">
                  <input
                    id="disable-audio"
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
              disabled={!audioEnabled}
            />
          </>
        ) : (
          <>
            <div className="section-title">{t('audio_settings.audio_section')}</div>
            <div className="settings-grid">
              <div className="setting-item">
                <label htmlFor="audio-bitrate">{t('audio_settings.bitrate')}</label>
                <Dropdown
                  editable
                  value={audioBitrate}
                  onChange={setAudioBitrate}
                  placeholder={t('audio_settings.bitrate_placeholder')}
                  disabled={disableAudioSettings}
                  ariaLabel={t('audio_settings.bitrate')}
                  validate={BITRATE_REGEX.test.bind(BITRATE_REGEX)}
                  fallbackValue="192"
                  options={AUDIO_BITRATE_OPTIONS.map((br) => ({ value: br, label: br }))}
                />
              </div>
              <div className="setting-item">
                <label htmlFor="keep-metadata">
                  <input
                    id="keep-metadata"
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
