import { useEffect } from 'react'

export type ThemeMode = 'light' | 'dark' | 'system'

export type AccentColor =
  'trust-blue' | 'stable-green' | 'grounded-orange' | 'sophisticated-indigo' | 'clarity-teal'

// NOTE: この許可集合は backend/api/blueprints/settings.py の VALID_THEME_MODES /
// VALID_ACCENT_COLORS と常に同期させること（フロントエンドは renderer プロセス、
// バックエンドは別プロセスのため定数を共有できない）。片方を変更したら必ず両方を更新する。
export const ACCENT_COLORS: AccentColor[] = [
  'trust-blue',
  'stable-green',
  'grounded-orange',
  'sophisticated-indigo',
  'clarity-teal',
]

export function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system'
}

export function isAccentColor(value: unknown): value is AccentColor {
  return typeof value === 'string' && (ACCENT_COLORS as string[]).includes(value)
}

export function resolveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return mode
}

const THEME_MODE_STORAGE_KEY = 'ame-theme-mode'
const ACCENT_COLOR_STORAGE_KEY = 'ame-accent-color'

function storeValue(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // プライバシーモード等でストレージが無効な場合は永続化をスキップする（表示には影響しない）。
  }
}

export function useTheme(mode: ThemeMode, persist = false): void {
  useEffect(() => {
    const resolved = resolveTheme(mode)
    document.documentElement.setAttribute('data-theme', resolved)
    void window.electronAPI?.setThemeColor(mode)
    if (persist) {
      storeValue(THEME_MODE_STORAGE_KEY, mode)
    }
  }, [mode, persist])

  useEffect(() => {
    if (mode !== 'system') return
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (): void => {
      document.documentElement.setAttribute('data-theme', mql.matches ? 'dark' : 'light')
      void window.electronAPI?.setThemeColor('system')
    }
    mql.addEventListener('change', handleChange)
    return (): void => {
      mql.removeEventListener('change', handleChange)
    }
  }, [mode])
}

export function useAccentColor(accent: AccentColor | null, persist = false): void {
  useEffect(() => {
    if (!accent) return
    document.documentElement.setAttribute('data-accent', accent)
    if (persist) {
      storeValue(ACCENT_COLOR_STORAGE_KEY, accent)
    }
  }, [accent, persist])
}

export function useDocumentLang(lang: string): void {
  useEffect(() => {
    if (lang) {
      document.documentElement.lang = lang
    }
  }, [lang])
}
