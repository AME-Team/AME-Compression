import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Save, RefreshCw, Moon, Sun, Monitor, Check, Loader2 } from 'lucide-react'
import { api, initializeApi } from '../services/api'
import type { AppSettings } from '../types'
import {
  ACCENT_COLORS,
  isAccentColor,
  isThemeMode,
  resolveTheme,
  useAccentColor,
  useTheme,
  type AccentColor,
  type ThemeMode,
} from '../hooks/useTheme'
import Dropdown from '../components/Dropdown'

interface SettingsViewProps {
  onAppearanceChange?: (mode: ThemeMode, accent: AccentColor) => void
}

const DEFAULT_SETTINGS: AppSettings = {
  language: 'en',
  appearance_mode: 'system',
  accent_color: 'trust-blue',
  ffmpeg_path: '',
  default_output_dir: '',
}

// NOTE: 各アクセントの色は index.css の :root[data-accent='...'] / [data-theme='dark'] 定義と
// 常に同期させること（CSS は静的セレクタが必要なため TS と定数を共有できない）。
const ACCENT_SWATCH: Record<AccentColor, { light: string; dark: string }> = {
  'trust-blue': { light: '#005B99', dark: '#3B82C4' },
  'stable-green': { light: '#2D6A4F', dark: '#4F8A6E' },
  'grounded-orange': { light: '#C2410C', dark: '#DD6B3D' },
  'sophisticated-indigo': { light: '#4338CA', dark: '#7C79E8' },
  'clarity-teal': { light: '#0F766E', dark: '#2FA39A' },
}

const SettingsView: React.FC<SettingsViewProps> = ({ onAppearanceChange }) => {
  const { t, i18n } = useTranslation()
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useTheme(settings.appearance_mode)
  useAccentColor(settings.accent_color)
  const resolvedTheme = resolveTheme(settings.appearance_mode)

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    try {
      await initializeApi()
      const response = await api.get<AppSettings>('/settings')
      const fetched = response.data
      setSettings({
        ...DEFAULT_SETTINGS,
        ...fetched,
        appearance_mode: isThemeMode(fetched.appearance_mode)
          ? fetched.appearance_mode
          : DEFAULT_SETTINGS.appearance_mode,
        accent_color: isAccentColor(fetched.accent_color)
          ? fetched.accent_color
          : DEFAULT_SETTINGS.accent_color,
      })
    } catch (error) {
      console.error('Failed to fetch settings', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchSettings()
  }, [fetchSettings])

  const saveSettings = async (): Promise<void> => {
    setSaving(true)
    try {
      await api.post<unknown>('/settings', settings)
      setMessage(t('settings.saved'))

      void i18n.changeLanguage(settings.language)
      onAppearanceChange?.(settings.appearance_mode, settings.accent_color)

      setTimeout(() => {
        setMessage('')
      }, 3000)
    } catch (error) {
      console.error('Failed to save settings', error)
      setMessage(t('common.error'))
    } finally {
      setSaving(false)
    }
  }

  const handleLanguageChange = (lang: string): void => {
    setSettings({ ...settings, language: lang })
  }

  const handleThemeChange = (mode: 'light' | 'dark' | 'system'): void => {
    setSettings({ ...settings, appearance_mode: mode })
  }

  const handleAccentChange = (accent: AccentColor): void => {
    setSettings({ ...settings, accent_color: accent })
  }

  if (loading) {
    return (
      <div className="loading-screen" role="status" aria-live="polite">
        <Loader2 size={20} className="spin" />
      </div>
    )
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.settings')}</h1>
        <p>{t('settings.title')}</p>
      </header>

      <section className="card">
        <h2>{t('settings.section_appearance')}</h2>
        <div className="settings-grid">
          <div className="setting-item">
            <label htmlFor="language-select">{t('settings.language')}</label>
            <Dropdown
              id="language-select"
              value={settings.language}
              onChange={(val) => {
                handleLanguageChange(val)
              }}
              ariaLabel={t('settings.language')}
              options={[
                { value: 'en', label: t('settings.language_names.en') },
                { value: 'ja', label: t('settings.language_names.ja') },
              ]}
            />
          </div>
          <div className="setting-item">
            <label>{t('settings.theme')}</label>
            <div className="theme-toggle" role="radiogroup" aria-label={t('settings.theme')}>
              <button
                className={`theme-button ${settings.appearance_mode === 'light' ? 'active' : ''}`}
                onClick={() => {
                  handleThemeChange('light')
                }}
                role="radio"
                aria-checked={settings.appearance_mode === 'light'}
              >
                <Sun size={16} /> {t('settings.themes.light')}
              </button>
              <button
                className={`theme-button ${settings.appearance_mode === 'dark' ? 'active' : ''}`}
                onClick={() => {
                  handleThemeChange('dark')
                }}
                role="radio"
                aria-checked={settings.appearance_mode === 'dark'}
              >
                <Moon size={16} /> {t('settings.themes.dark')}
              </button>
              <button
                className={`theme-button ${settings.appearance_mode === 'system' ? 'active' : ''}`}
                onClick={() => {
                  handleThemeChange('system')
                }}
                role="radio"
                aria-checked={settings.appearance_mode === 'system'}
              >
                <Monitor size={16} /> {t('settings.themes.system')}
              </button>
            </div>
          </div>
          <div className="setting-item span-full">
            <label>{t('settings.accent_color')}</label>
            <div
              className="accent-swatches"
              role="radiogroup"
              aria-label={t('settings.accent_color')}
            >
              {ACCENT_COLORS.map((accent) => {
                const swatch = ACCENT_SWATCH[accent]
                const selected = settings.accent_color === accent
                return (
                  <button
                    key={accent}
                    className={`accent-swatch ${selected ? 'active' : ''}`}
                    onClick={() => {
                      handleAccentChange(accent)
                    }}
                    role="radio"
                    aria-checked={selected}
                    aria-label={t(`settings.accent_colors.${accent}`)}
                    title={t(`settings.accent_colors.${accent}`)}
                  >
                    <span
                      className="accent-swatch-color"
                      style={{ backgroundColor: swatch[resolvedTheme] }}
                    />
                    {selected && (
                      <span className="accent-swatch-check">
                        <Check size={12} />
                      </span>
                    )}
                    <span className="accent-swatch-label">
                      {t(`settings.accent_colors.${accent}`)}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <h2>{t('settings.section_ffmpeg')}</h2>
        <div className="settings-grid">
          <div className="setting-item span-full">
            <label htmlFor="ffmpeg-path">{t('settings.ffmpeg_path')}</label>
            <div className="input-with-button">
              <input
                id="ffmpeg-path"
                type="text"
                value={settings.ffmpeg_path}
                onChange={(e) => {
                  setSettings({ ...settings, ffmpeg_path: e.target.value })
                }}
                placeholder={t('settings.auto_detect')}
              />
            </div>
          </div>
        </div>

        <h2>{t('settings.section_output')}</h2>
        <div className="settings-grid">
          <div className="setting-item span-full">
            <label htmlFor="output-dir">{t('settings.output_default')}</label>
            <input
              id="output-dir"
              type="text"
              value={settings.default_output_dir}
              onChange={(e) => {
                setSettings({ ...settings, default_output_dir: e.target.value })
              }}
              placeholder={t('settings.output_placeholder')}
            />
          </div>
        </div>

        <div className="settings-actions">
          <button className="primary-button" onClick={() => void saveSettings()} disabled={saving}>
            {saving ? <RefreshCw className="spin" size={16} /> : <Save size={16} />}
            {t('settings.save')}
          </button>
          {message && (
            <span className="status-message" role="status" aria-live="polite">
              {message}
            </span>
          )}
        </div>
      </section>
    </div>
  )
}

export default SettingsView
