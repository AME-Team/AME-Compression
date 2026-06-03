import React from 'react'
import { useTranslation } from 'react-i18next'
import { X, CheckCircle, XCircle, Loader2, Clock, AlertCircle, Play } from 'lucide-react'
import type { Job } from '../types'

interface JobItemProps {
  job: Job
  onCancel: (id: string) => void
  onDismiss: (id: string) => void
}

const STATUS_CONFIG: Record<
  string,
  { icon: React.ReactNode; labelKey: string; ariaLabelKey: string }
> = {
  starting: {
    icon: <Play size={12} />,
    labelKey: 'status.starting',
    ariaLabelKey: 'status.starting',
  },
  running: {
    icon: <Loader2 size={12} className="spin" />,
    labelKey: 'status.running',
    ariaLabelKey: 'status.running',
  },
  success: {
    icon: <CheckCircle size={12} />,
    labelKey: 'status.success',
    ariaLabelKey: 'status.success',
  },
  failed: {
    icon: <XCircle size={12} />,
    labelKey: 'status.failed',
    ariaLabelKey: 'status.failed',
  },
}

const JobItem: React.FC<JobItemProps> = ({ job, onCancel, onDismiss }) => {
  const { t } = useTranslation()

  const statusConfig = STATUS_CONFIG[job.status]
  const statusLabel = statusConfig ? t(statusConfig.labelKey) : job.status

  return (
    <div className={`job-item ${job.status}`} role="listitem">
      <div className="job-info">
        <span className="job-type">{job.type === 'video' ? 'Video' : 'Audio'}</span>
        {job.filename && (
          <span className="job-filename" title={job.filename}>
            {job.filename}
          </span>
        )}
        <span className={`job-status-badge ${job.status}`} role="status" aria-label={statusLabel}>
          {statusConfig?.icon}
          {statusLabel}
        </span>
      </div>

      {job.status === 'running' && job.progress && (
        <div className="job-progress" aria-live="polite">
          <div className="progress-bar-wrapper">
            <div
              className="progress-bar-bg"
              role="progressbar"
              aria-valuenow={Math.round(job.progress.percent)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${Math.round(job.progress.percent)}%`}
            >
              <div
                className="progress-bar-fill"
                style={{ width: `${Math.min(100, job.progress.percent)}%` }}
              />
            </div>
            <span className="progress-percent">{Math.round(job.progress.percent)}%</span>
          </div>
          <div className="job-stats">
            <span className="stat-item">
              <Clock size={10} />
              <span className="stat-label">{t('compress.eta')}:</span>
              <span className="stat-value">{formatTimeShort(job.progress.eta) || '---'}</span>
            </span>
            {job.progress.speed !== undefined && job.progress.speed > 0 && (
              <span className="stat-item">
                <span className="stat-label">{t('compress.speed')}:</span>
                <span className="stat-value">{job.progress.speed.toFixed(1)}x</span>
              </span>
            )}
            {job.progress.fps !== undefined && job.progress.fps > 0 && (
              <span className="stat-item">
                <span className="stat-label">{t('compress.fps')}:</span>
                <span className="stat-value">{Math.round(job.progress.fps)}</span>
              </span>
            )}
          </div>
          <div className="job-stats secondary-stats">
            {job.progress.current_time !== undefined &&
              job.progress.current_time >= 0 &&
              job.progress.total_duration !== undefined &&
              job.progress.total_duration > 0 && (
                <span className="stat-item">
                  <span className="stat-label">{t('compress.time_position')}:</span>
                  <span className="stat-value">
                    {formatTime(job.progress.current_time)} /{' '}
                    {formatTime(job.progress.total_duration)}
                  </span>
                </span>
              )}
            {job.progress.frame !== undefined && job.progress.frame >= 0 && (
              <span className="stat-item">
                <span className="stat-label">{t('compress.frame')}:</span>
                <span className="stat-value">{job.progress.frame.toLocaleString()}</span>
              </span>
            )}
          </div>
        </div>
      )}

      {job.status === 'success' && job.result && (
        <div className="job-result">
          <span className="result-compression" aria-label={t('compress.reduction')}>
            <CheckCircle size={12} /> -{job.result.compression_ratio?.toFixed(1)}%{' '}
            {t('compress.reduction')}
          </span>
        </div>
      )}

      {job.status === 'failed' && (
        <div className="job-result">
          <span className="result-compression" style={{ color: 'var(--color-error)' }}>
            <AlertCircle size={12} /> {t('compress.failed')}
          </span>
        </div>
      )}

      {(job.status === 'running' || job.status === 'starting') && (
        <button
          className="cancel-button job-action-button"
          onClick={() => {
            onCancel(job.id)
          }}
          aria-label={t('compress.cancel')}
        >
          <X size={14} />
        </button>
      )}

      {(job.status === 'success' || job.status === 'failed') && (
        <button
          className="dismiss-button job-action-button"
          onClick={() => {
            onDismiss(job.id)
          }}
          aria-label={t('compress.dismiss')}
        >
          <X size={14} />
        </button>
      )}
    </div>
  )
}

interface ProgressPanelProps {
  jobs: Job[]
  onCancel: (id: string) => void
  onDismiss: (id: string) => void
  onClosePanel?: () => void
  embedded?: boolean
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '--:--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatTimeShort(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({
  jobs,
  onCancel,
  onDismiss,
  onClosePanel,
  embedded = false,
}) => {
  const { t } = useTranslation()

  if (embedded) {
    if (jobs.length === 0) return null
    return (
      <div
        className="job-list"
        style={{ maxHeight: 'none', overflowY: 'visible' }}
        role="list"
        aria-label={t('compress.progress')}
      >
        {jobs.map((job) => (
          <JobItem key={job.id} job={job} onCancel={onCancel} onDismiss={onDismiss} />
        ))}
      </div>
    )
  }

  if (jobs.length === 0) return null

  return (
    <div className="progress-panel">
      <div className="progress-panel-header">
        <h3>{t('compress.progress')}</h3>
        <button
          className="panel-close-button"
          onClick={() => onClosePanel?.()}
          aria-label={t('compress.dismiss')}
        >
          <X size={16} />
        </button>
      </div>
      <div className="job-list" role="list" aria-label={t('compress.progress')}>
        {jobs.map((job) => (
          <JobItem key={job.id} job={job} onCancel={onCancel} onDismiss={onDismiss} />
        ))}
      </div>
    </div>
  )
}

export { ProgressPanel }
export default ProgressPanel
