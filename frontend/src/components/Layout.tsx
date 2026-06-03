import React, { useRef, useCallback } from 'react'
import Sidebar from './Sidebar'

interface LayoutProps {
  children: React.ReactNode
  activeView: string
  onViewChange: (view: string) => void
}

const Layout: React.FC<LayoutProps> = ({ children, activeView, onViewChange }) => {
  const mainRef = useRef<HTMLDivElement>(null)

  const handleSkipToContent = useCallback((e: React.KeyboardEvent<HTMLAnchorElement>): void => {
    if (e.key === 'Enter') {
      mainRef.current?.focus()
    }
  }, [])

  return (
    <div className="app-container">
      <a href="#main-content" className="skip-to-content" onKeyDown={handleSkipToContent}>
        Skip to main content
      </a>
      <Sidebar activeView={activeView} onViewChange={onViewChange} />
      <main id="main-content" className="main-content" ref={mainRef} tabIndex={-1}>
        {children}
      </main>
    </div>
  )
}

export default Layout
