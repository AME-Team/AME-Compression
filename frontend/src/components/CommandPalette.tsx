import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Play, Settings, RotateCcw, Layers } from 'lucide-react'

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  onNavigate: (view: string) => void
  onStartCompression: () => void
}

interface CommandItem {
  id: string
  label: string
  icon: React.ReactNode
  action: () => void
}

const CommandPalette: React.FC<CommandPaletteProps> = ({
  open,
  onClose,
  onNavigate,
  onStartCompression,
}) => {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const commands: CommandItem[] = [
    {
      id: 'nav-media',
      label: t('nav.video_audio'),
      icon: <Layers size={16} />,
      action: () => {
        onNavigate('media')
        onClose()
      },
    },
    {
      id: 'nav-settings',
      label: t('nav.settings'),
      icon: <Settings size={16} />,
      action: () => {
        onNavigate('settings')
        onClose()
      },
    },
    {
      id: 'start-compression',
      label: t('compress.start'),
      icon: <Play size={16} />,
      action: () => {
        onStartCompression()
        onClose()
      },
    },
    {
      id: 'reset-defaults',
      label: t('profile.load_defaults'),
      icon: <RotateCcw size={16} />,
      action: () => {
        onClose()
      },
    },
  ]

  const filtered = commands.filter((cmd) => cmd.label.toLowerCase().includes(query.toLowerCase()))

  useEffect(() => {
    if (open) {
      setQuery('')
      setActiveIndex(0)
      setTimeout(() => {
        inputRef.current?.focus()
      }, 0)
    }
  }, [open])

  useEffect(() => {
    setActiveIndex(0)
  }, [query])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent): void => {
      if (e.key === 'Escape') {
        onClose()
        return
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setActiveIndex((prev) => Math.min(prev + 1, filtered.length - 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setActiveIndex((prev) => Math.max(prev - 1, 0))
        return
      }
      if (e.key === 'Enter' && filtered[activeIndex]) {
        filtered[activeIndex].action()
        return
      }
    },
    [filtered, activeIndex, onClose],
  )

  useEffect(() => {
    if (!open) return
    const activeItem = listRef.current?.querySelector(`[data-index="${activeIndex}"]`)
    activeItem?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex, open])

  if (!open) return null

  return (
    <div
      className="command-palette-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={t('command_palette.title')}
    >
      <div
        className="command-palette-dialog"
        onClick={(e) => {
          e.stopPropagation()
        }}
        onKeyDown={handleKeyDown}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '0 16px' }}>
          <Search size={16} style={{ color: '#737373', flexShrink: 0 }} />
          <input
            ref={inputRef}
            className="command-palette-input"
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
            }}
            placeholder={t('command_palette.placeholder')}
            autoFocus
            aria-label={t('command_palette.placeholder')}
          />
        </div>
        <div className="command-palette-list" ref={listRef} role="listbox">
          {filtered.length === 0 && (
            <div
              style={{
                padding: '20px',
                textAlign: 'center',
                color: '#737373',
                fontSize: '0.85rem',
              }}
            >
              {t('command_palette.no_results')}
            </div>
          )}
          {filtered.map((cmd, index) => (
            <button
              key={cmd.id}
              className={`command-palette-item ${index === activeIndex ? 'active' : ''}`}
              onClick={cmd.action}
              role="option"
              aria-selected={index === activeIndex}
              data-index={index}
            >
              {cmd.icon}
              <span style={{ flex: 1 }}>{cmd.label}</span>
            </button>
          ))}
        </div>
        <div className="command-palette-footer">
          <span className="kbd">&#8593;&#8595;</span> {t('command_palette.navigate')}
          <span className="kbd">Enter</span> {t('command_palette.select')}
          <span className="kbd">Esc</span> {t('command_palette.close')}
        </div>
      </div>
    </div>
  )
}

export default CommandPalette
