export type JobStatus = 'starting' | 'running' | 'success' | 'failed' | 'pending'
export type JobType = 'video' | 'audio'

export interface Progress {
  percent: number
  eta: number
  speed?: number
  current_time?: number
  total_duration?: number
  fps?: number
  frame?: number
}

export interface TaskResult {
  compression_ratio?: number
  output_size?: number
  duration?: number
  bitrate?: number
  [key: string]: unknown
}

export interface Job {
  id: string
  status: JobStatus
  progress: Progress | null
  result: TaskResult | null
  type: JobType
  filename: string
}

export interface MediaInfo {
  type: 'video' | 'audio'
  duration: number
  width?: number
  height?: number
  bitrate?: number
}

export interface AppSettings {
  language: string
  appearance_mode: 'light' | 'dark' | 'system'
  accent_color:
    'trust-blue' | 'stable-green' | 'grounded-orange' | 'sophisticated-indigo' | 'clarity-teal'
  ffmpeg_path: string
  default_output_dir: string
}

export type AnalysisMode = 'none' | 'all' | 'video' | 'audio'

export interface QualityAnalysisResult {
  status: 'success' | 'error' | 'skipped'
  recommended_crf: number | null
  recommend_denoise: boolean | null
  denoise_level: number | null
  recommended_volume_gain?: number | null
  bpp: number | null
  reason: string
  path?: string
  media_type?: 'video' | 'audio' | 'unknown'
  recommended_bitrate?: number
  metadata: {
    width?: number | null
    height?: number | null
    fps?: number | null
    duration?: number | null
    bit_rate?: number | null
    codec_name?: string
    sample_rate?: number | null
    channels?: number | null
  }
}

export interface BatchAnalysisItem {
  path: string
  result: QualityAnalysisResult
}
