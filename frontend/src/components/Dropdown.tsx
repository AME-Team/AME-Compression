import React, { useState, useEffect, useRef, useCallback, useId } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown } from 'lucide-react'

interface DropdownOption {
  value: string
  label: string
}

interface DropdownProps {
  id?: string
  value: string
  onChange: (val: string) => void
  options: DropdownOption[]
  disabled?: boolean
  ariaLabel?: string
  editable?: boolean
  placeholder?: string
  sanitize?: (val: string) => string
  validate?: (val: string) => boolean
  fallbackValue?: string
}

const Dropdown: React.FC<DropdownProps> = ({
  id,
  value,
  onChange,
  options = [],
  disabled,
  ariaLabel,
  editable = false,
  placeholder,
  sanitize,
  validate,
  fallbackValue,
}) => {
  const { t } = useTranslation()
  const listboxId = useId()
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const [invalid, setInvalid] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const justSelectedRef = useRef(false)
  const listRef = useRef<HTMLUListElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedLabel = options.find((o) => o.value === value)?.label ?? value

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent): void => {
      if (
        containerRef.current &&
        e.target instanceof Element &&
        !containerRef.current.contains(e.target)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return (): void => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  useEffect(() => {
    if (!open) return
    const index = options.findIndex((o) => o.value === value)
    setActiveIndex(index)
  }, [open, value, options])

  useEffect(() => {
    if (!open) return
    listRef.current?.querySelector(`[data-index="${activeIndex}"]`)?.scrollIntoView({
      block: 'nearest',
    })
  }, [activeIndex, open])

  const close = useCallback((): void => {
    setOpen(false)
    if (editable) {
      inputRef.current?.focus()
    } else {
      triggerRef.current?.focus()
    }
  }, [editable])

  const selectOption = useCallback(
    (opt: DropdownOption): void => {
      justSelectedRef.current = true
      onChange(opt.value)
      setInvalid(false)
      close()
    },
    [onChange, close],
  )

  const handleTriggerKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Escape') {
      close()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!open) {
        setOpen(true)
        return
      }
      setActiveIndex((prev) => Math.min(prev + 1, options.length - 1))
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (!open) {
        setOpen(true)
        return
      }
      setActiveIndex((prev) => Math.max(prev - 1, 0))
      return
    }
    if (e.key === 'Home') {
      e.preventDefault()
      setActiveIndex(0)
      return
    }
    if (e.key === 'End') {
      e.preventDefault()
      setActiveIndex(options.length - 1)
      return
    }
    if (e.key === 'Enter' || e.key === ' ') {
      if (!open) {
        e.preventDefault()
        setOpen(true)
        return
      }
      const option = options[activeIndex]
      if (option) {
        e.preventDefault()
        selectOption(option)
      }
      return
    }
    if (e.key === 'Tab') {
      setOpen(false)
    }
  }

  const handleEditableKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Escape') {
      close()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
      setActiveIndex((prev) => Math.min(prev + 1, options.length - 1))
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((prev) => Math.max(prev - 1, 0))
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      if (open) {
        const targetIndex =
          activeIndex >= 0 ? activeIndex : options.findIndex((o) => o.value === value)
        const option = options[targetIndex]
        if (option) {
          selectOption(option)
        } else {
          commitEditableValue(value)
          setOpen(false)
        }
      } else {
        commitEditableValue(value)
        setOpen(false)
      }
      return
    }
    if (e.key === 'Tab') {
      setOpen(false)
    }
  }

  const commitEditableValue = useCallback(
    (val: string): void => {
      if (validate && !validate(val)) {
        onChange(fallbackValue ?? '')
        setInvalid(true)
      } else {
        onChange(val)
        setInvalid(false)
      }
    },
    [validate, fallbackValue, onChange],
  )

  const handleEditableBlur = (e: React.FocusEvent<HTMLInputElement>): void => {
    if (justSelectedRef.current) {
      justSelectedRef.current = false
      setOpen(false)
      return
    }
    commitEditableValue(e.target.value)
    setOpen(false)
  }

  const listboxProps = {
    id: listboxId,
    role: 'listbox' as const,
    'aria-label': ariaLabel,
  }

  return (
    <div ref={containerRef} className="combobox">
      {editable ? (
        <div className="combobox-input-group">
          <input
            ref={inputRef}
            id={id}
            type="text"
            value={value}
            placeholder={placeholder}
            disabled={disabled}
            onChange={(e) => {
              const sanitized = sanitize ? sanitize(e.target.value) : e.target.value
              onChange(sanitized)
              setInvalid(false)
            }}
            onBlur={handleEditableBlur}
            onKeyDown={handleEditableKeyDown}
            className="combobox-input"
            role="combobox"
            aria-expanded={open}
            aria-haspopup="listbox"
            aria-controls={listboxId}
            aria-invalid={invalid || undefined}
            aria-activedescendant={
              open && options.length > 0 && activeIndex >= 0
                ? `${listboxId}-${activeIndex}`
                : undefined
            }
            aria-label={ariaLabel}
          />
          <button
            type="button"
            className="secondary-button combobox-toggle"
            disabled={disabled}
            onClick={() => {
              if (open) {
                setOpen(false)
              } else {
                setOpen(true)
                inputRef.current?.focus()
              }
            }}
            aria-label={t('a11y.toggle_dropdown')}
          >
            <ChevronDown size={14} />
          </button>
        </div>
      ) : (
        <button
          ref={triggerRef}
          id={id}
          type="button"
          className="select-dropdown-trigger"
          disabled={disabled}
          onClick={() => {
            setOpen(!open)
          }}
          onKeyDown={handleTriggerKeyDown}
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listboxId}
          aria-activedescendant={
            open && options.length > 0 && activeIndex >= 0
              ? `${listboxId}-${activeIndex}`
              : undefined
          }
          aria-label={ariaLabel}
        >
          <span className="select-dropdown-value">{selectedLabel}</span>
          <ChevronDown size={14} className="select-dropdown-chevron" />
        </button>
      )}
      {open && options.length > 0 && (
        <ul ref={listRef} className="combobox-dropdown" {...listboxProps}>
          {options.map((opt, index) => (
            <li
              key={opt.value}
              id={`${listboxId}-${index}`}
              role="option"
              aria-selected={value === opt.value}
              data-index={index}
              onClick={(): void => {
                selectOption(opt)
              }}
              onMouseEnter={(): void => {
                setActiveIndex(index)
              }}
              className={`combobox-option${value === opt.value ? ' selected' : ''}${
                activeIndex === index ? ' active' : ''
              }`}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Dropdown
