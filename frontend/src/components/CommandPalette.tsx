import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Play, Settings, RotateCcw, Layers } from 'lucide-react'
import { useFocusTrap } from '../hooks/useFocusTrap'

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  onNavigate: (view: string) => void
  onStartCompression: () => void
  onApplyDefaults: () => void
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
  onApplyDefaults,
}) => {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  useFocusTrap(dialogRef, open)

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
        onApplyDefaults()
        onClose()
      },
    },
  ]

  const filtered = commands.filter((cmd) => cmd.label.toLowerCase().includes(query.toLowerCase()))
  const activeCommand = activeIndex < filtered.length ? filtered[activeIndex] : undefined

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
      }
    },
    [filtered, activeIndex, onClose],
  )

  useEffect(() => {
    if (!open) return
    dialogRef.current?.querySelector(`[data-index="${activeIndex}"]`)?.scrollIntoView({
      block: 'nearest',
    })
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
        ref={dialogRef}
        onClick={(e) => {
          e.stopPropagation()
        }}
        onKeyDown={handleKeyDown}
      >
        <div className="command-palette-search">
          <Search size={16} className="command-palette-search-icon" />
          <input
            ref={inputRef}
            className="command-palette-input"
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
            }}
            placeholder={t('command_palette.placeholder')}
            aria-label={t('command_palette.placeholder')}
            aria-controls="command-palette-listbox"
            aria-activedescendant={activeCommand ? `command-item-${activeCommand.id}` : undefined}
          />
        </div>
        <div id="command-palette-listbox" className="command-palette-list" role="listbox">
          {filtered.length === 0 && (
            <div className="command-palette-empty">{t('command_palette.no_results')}</div>
          )}
          {filtered.map((cmd, index) => (
            <button
              key={cmd.id}
              id={`command-item-${cmd.id}`}
              className={`command-palette-item ${index === activeIndex ? 'active' : ''}`}
              onClick={cmd.action}
              role="option"
              aria-selected={index === activeIndex}
              data-index={index}
            >
              {cmd.icon}
              <span className="command-palette-item-label">{cmd.label}</span>
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
