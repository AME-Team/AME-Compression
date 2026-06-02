import React, { useEffect, useRef, useCallback } from 'react'

interface ConfirmModalProps {
  open: boolean
  title: string
  message: string
  confirmLabel: string
  cancelLabel?: string
  variant: 'warning' | 'danger' | 'info'
  onConfirm: () => void
  onCancel: () => void
  showCancel?: boolean
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  variant,
  onConfirm,
  onCancel,
  showCancel = true,
}) => {
  const modalRef = useRef<HTMLDivElement>(null)
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  const handleKeyDown = useCallback(
    (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        onCancel()
        return
      }

      if (e.key !== 'Tab' || !modalRef.current) return

      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      )
      const focusable = Array.from(focusableElements)
      if (focusable.length === 0) return

      const firstEl = focusable[0]
      const lastEl = focusable[focusable.length - 1]

      if (!firstEl || !lastEl) return

      if (e.shiftKey) {
        if (document.activeElement === firstEl) {
          e.preventDefault()
          lastEl.focus()
        }
      } else {
        if (document.activeElement === lastEl) {
          e.preventDefault()
          firstEl.focus()
        }
      }
    },
    [onCancel],
  )

  useEffect(() => {
    if (!open) return
    document.addEventListener('keydown', handleKeyDown)
    confirmButtonRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, handleKeyDown])

  if (!open) return null

  return (
    <div className="modal-overlay confirm-modal-overlay" onClick={onCancel}>
      <div
        className="modal-content confirm-modal-content"
        ref={modalRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        aria-describedby="confirm-modal-message"
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        <div className="modal-header">
          <h3 id="confirm-modal-title">{title}</h3>
        </div>
        <div className="modal-body">
          <p id="confirm-modal-message" className="confirm-modal-message">
            {message}
          </p>
        </div>
        <div className="modal-footer">
          {showCancel && (
            <button ref={cancelButtonRef} className="secondary-button" onClick={onCancel}>
              {cancelLabel}
            </button>
          )}
          <button
            ref={confirmButtonRef}
            className={`primary-button confirm-btn-${variant}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmModal
