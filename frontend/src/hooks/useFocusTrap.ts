import { useEffect } from 'react'

const FOCUSABLE_SELECTOR =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * Traps focus inside the element referenced by `ref` while `active` is true,
 * and restores focus to the previously focused element on deactivation.
 */
export function useFocusTrap(ref: React.RefObject<HTMLElement | null>, active: boolean): void {
  useEffect(() => {
    if (!active) return
    const container = ref.current
    if (!container) return

    const previousActiveElement = document.activeElement

    const focusable = Array.from(
      container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
    ).filter((el) => !el.hasAttribute('disabled'))
    const first = focusable[0]
    if (first) {
      first.focus()
    }

    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key !== 'Tab') return
      const currentFocusable = Array.from(
        container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      ).filter((el) => !el.hasAttribute('disabled'))
      if (currentFocusable.length === 0) {
        e.preventDefault()
        return
      }
      const firstEl = currentFocusable[0]
      const lastEl = currentFocusable[currentFocusable.length - 1]
      if (!firstEl || !lastEl) return

      if (e.shiftKey) {
        if (document.activeElement === firstEl || !container.contains(document.activeElement)) {
          e.preventDefault()
          lastEl.focus()
        }
      } else if (document.activeElement === lastEl || !container.contains(document.activeElement)) {
        e.preventDefault()
        firstEl.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      if (previousActiveElement instanceof HTMLElement) {
        previousActiveElement.focus()
      }
    }
  }, [ref, active])
}
