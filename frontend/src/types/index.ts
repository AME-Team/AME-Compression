export type JobStatus = 'starting' | 'running' | 'success' | 'failed'
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
  ffmpeg_path: string
  default_output_dir: string
}

export interface QualityAnalysisResult {
  status: 'success' | 'error'
  recommended_crf: number
  recommend_denoise: boolean
  denoise_level: number | null
  bpp: number
  reason: string
  metadata: {
    width?: number | null
    height?: number | null
    fps?: number | null
    duration?: number | null
    bit_rate?: number | null
    codec_name?: string
  }
}
