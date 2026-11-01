import type { CompressionMode, TargetSizeMode } from './types'

export interface MediaProfile {
  name: string
  mediaType: 'video' | 'audio'
  compressionMode?: CompressionMode
  targetSizeMode?: TargetSizeMode
  targetSizeMb?: string
  targetSizePercent?: number
  crf: number
  preset: number
  maxResolution: string
  customWidth: string
  customHeight: string
  maxFps: string
  videoAudioBitrate: string
  audioEnabled: boolean
  audioBitrate: string
  keepMetadata: boolean
  volumeMode: string
  volumeValue: number
  denoiseEnabled: boolean
  denoiseLevel: number
  /** SVT-AV1 tune=0 + enable-qm=1 (perceptual quality tuning). */
  visualTuning?: boolean
  /** Encode to a 10-bit pixel format instead of the source depth. */
  tenBit?: boolean
}

export const PROFILE_STORAGE_KEY = 'ame-media-profiles'

/**
 * Defaults for the SVT-AV1 encoder options. Mirrored in backend/config.py as
 * DEFAULT_VISUAL_TUNING / DEFAULT_TEN_BIT; keep both sides in sync.
 */
export const DEFAULT_VISUAL_TUNING = true
export const DEFAULT_TEN_BIT = false

export const DEFAULT_SETTINGS: Omit<MediaProfile, 'name'> = {
  mediaType: 'video',
  compressionMode: 'crf',
  targetSizeMode: 'percent',
  targetSizeMb: '100',
  targetSizePercent: 50,
  crf: 25,
  preset: 6,
  maxResolution: 'original',
  customWidth: '',
  customHeight: '',
  maxFps: 'unlimited',
  videoAudioBitrate: '192',
  audioEnabled: true,
  audioBitrate: '192',
  keepMetadata: true,
  volumeMode: 'disabled',
  volumeValue: 0,
  denoiseEnabled: false,
  denoiseLevel: 0.15,
  visualTuning: DEFAULT_VISUAL_TUNING,
  tenBit: DEFAULT_TEN_BIT,
}

export function loadProfiles(): MediaProfile[] {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveProfiles(profiles: MediaProfile[]): void {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profiles))
}
