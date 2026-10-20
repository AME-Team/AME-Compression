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
}

export const PROFILE_STORAGE_KEY = 'ame-media-profiles'

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
