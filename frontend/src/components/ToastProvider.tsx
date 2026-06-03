import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { ToastContext, type ToastVariant } from './ToastContext'

interface ToastItem {
  id: string
  message: string
  variant: ToastVariant
}

const VARIANT_CONFIG: Record<ToastVariant, { icon: React.ReactNode; className: string }> = {
  success: {
    icon: <CheckCircle size={16} />,
    className: 'toast-success',
  },
  error: {
    icon: <AlertCircle size={16} />,
    className: 'toast-error',
  },
  info: {
    icon: <Info size={16} />,
    className: 'toast-info',
  },
}

const TOAST_DURATION = 5000

const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { t } = useTranslation()
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  const removeToast = useCallback((id: string): void => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
    const timer = timersRef.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timersRef.current.delete(id)
    }
  }, [])

  const showToast = useCallback(
    (message: string, variant: ToastVariant = 'success'): void => {
      const id = crypto.randomUUID()
      setToasts((prev) => [...prev, { id, message, variant }])

      const timer = setTimeout(() => {
        removeToast(id)
      }, TOAST_DURATION)
      timersRef.current.set(id, timer)
    },
    [removeToast],
  )

  useEffect(() => {
    const timers = timersRef.current
    return () => {
      for (const timer of timers.values()) {
        clearTimeout(timer)
      }
      timers.clear()
    }
  }, [])

  return (
    <ToastContext value={{ showToast }}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="false"
        aria-label={t('a11y.notifications')}
        style={{
          position: 'fixed',
          bottom: '72px',
          right: '24px',
          zIndex: 400,
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {toasts.map((toast) => {
          const config = VARIANT_CONFIG[toast.variant]
          return (
            <div key={toast.id} className={`toast-notification ${config.className}`} role="status">
              {config.icon}
              <span style={{ flex: 1 }}>{toast.message}</span>
              <button
                className="toast-close-btn"
                onClick={() => {
                  removeToast(toast.id)
                }}
                aria-label={t('common.close')}
              >
                <X size={14} />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext>
  )
}

export default ToastProvider
