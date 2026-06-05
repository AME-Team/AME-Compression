import React, { useState, useEffect, useRef } from 'react'
import { ChevronDown } from 'lucide-react'

interface SelectDropdownProps {
  value: string
  onChange: (val: string) => void
  options: { value: string; label: string }[]
  disabled?: boolean
  ariaLabel?: string
}

const SelectDropdown: React.FC<SelectDropdownProps> = ({
  value,
  onChange,
  options,
  disabled,
  ariaLabel,
}) => {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

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

  const selectedLabel = options.find((o) => o.value === value)?.label ?? value

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <button
        type="button"
        className="select-dropdown-trigger"
        disabled={disabled}
        onClick={() => {
          setOpen(!open)
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <span className="select-dropdown-value">{selectedLabel}</span>
        <ChevronDown size={14} className="select-dropdown-chevron" />
      </button>
      {open && (
        <ul role="listbox" className="combobox-dropdown">
          {options.map((opt) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={value === opt.value}
              onClick={(): void => {
                onChange(opt.value)
                setOpen(false)
              }}
              className="combobox-option"
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                background: value === opt.value ? 'var(--color-primary)' : 'transparent',
                color: value === opt.value ? '#fff' : 'inherit',
                fontSize: '0.85rem',
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default SelectDropdown
