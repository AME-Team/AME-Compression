import React from 'react'
import { useTranslation } from 'react-i18next'
import { Settings, Layers } from 'lucide-react'
import logoSvg from '../assets/logo.svg'

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, onViewChange }) => {
  const { t } = useTranslation()

  const navItems = [
    { id: 'media', icon: <Layers size={18} />, label: t('nav.video_audio') },
    { id: 'settings', icon: <Settings size={18} />, label: t('nav.settings') },
  ]

  return (
    <aside className="sidebar" role="navigation" aria-label={t('nav.main_navigation')}>
      <div className="sidebar-header">
        <img src={logoSvg} alt={t('app.title')} className="sidebar-logo" />
        <h2>{t('app.title')}</h2>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
            onClick={() => {
              onViewChange(item.id)
            }}
            aria-current={activeView === item.id ? 'page' : undefined}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span>v1.0.6</span>
      </div>
    </aside>
  )
}

export default Sidebar
