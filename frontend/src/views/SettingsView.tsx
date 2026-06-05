import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Save, RefreshCw, Moon, Sun, Monitor } from 'lucide-react'
import { api, initializeApi } from '../services/api'
import type { AppSettings } from '../types'
import SelectDropdown from '../components/SelectDropdown'

const SettingsView: React.FC = () => {
  const { t, i18n } = useTranslation()
  const [settings, setSettings] = useState<AppSettings>({
    language: 'en',
    appearance_mode: 'system',
    ffmpeg_path: '',
    default_output_dir: '',
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    try {
      await initializeApi()
      const response = await api.get<AppSettings>('/settings')
      setSettings(response.data)
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

      document.documentElement.setAttribute('data-theme', settings.appearance_mode)

      void window.electronAPI?.setThemeColor(settings.appearance_mode)

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
    const resolvedTheme =
      mode === 'system'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : mode
    document.documentElement.setAttribute('data-theme', resolvedTheme)
    void window.electronAPI?.setThemeColor(mode)
  }

  if (loading) return <div>{t('common.loading')}</div>

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>{t('nav.settings')}</h1>
        <p>{t('settings.title')}</p>
      </header>

      <section className="card">
        <div className="section-title">{t('settings.section_appearance')}</div>
        <div className="settings-grid">
          <div className="setting-item">
            <label htmlFor="language-select">{t('settings.language')}</label>
            <SelectDropdown
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
        </div>

        <div className="section-title">{t('settings.section_ffmpeg')}</div>
        <div className="settings-grid">
          <div className="setting-item" style={{ gridColumn: '1 / -1' }}>
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

        <div className="section-title">{t('settings.section_output')}</div>
        <div className="settings-grid">
          <div className="setting-item" style={{ gridColumn: '1 / -1' }}>
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
