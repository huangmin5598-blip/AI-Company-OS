'use client'

import { useState, useRef, useEffect } from 'react'
import { usePathname } from 'next/navigation'

type NavItem = {
  label: string
  href: string
}

type Tab = {
  id: string
  label: string
  icon: string
  items: NavItem[]
}

const TABS: Tab[] = [
  {
    id: 'dashboard',
    label: '总览',
    icon: '📊',
    items: [
      { label: '系统状态', href: '/' },
      { label: 'CEO', href: '/ceo' },
      { label: 'CEO 目标', href: '/ceo/goals' },
      { label: 'CEO 日志', href: '/ceo/logs' },
      { label: '执行记录', href: '/runs' },
      { label: '运行闭环', href: '/loop' },
    ],
  },
  {
    id: 'workbench',
    label: '工作台',
    icon: '⚡',
    items: [
      { label: '任务看板', href: '/tasks' },
      { label: '任务池', href: '/task-pool' },
      { label: '执行桥', href: '/execution-requests' },
      { label: '指挥台', href: '/command' },
      { label: '对话', href: '/chat' },
    ],
  },
  {
    id: 'company',
    label: '公司能力',
    icon: '🧠',
    items: [
      { label: 'Agent', href: '/agents' },
      { label: '技能地图', href: '/skills' },
      { label: '记忆', href: '/memory' },
      { label: '分析', href: '/analysis' },
    ],
  },
  {
    id: 'products',
    label: '项目与产品',
    icon: '📦',
    items: [
      { label: '代码桥', href: '/code-change-requests' },
      { label: '改进提案', href: '/improvement-proposals' },
    ],
  },
  {
    id: 'governance',
    label: '治理与设置',
    icon: '⚙️',
    items: [
      { label: '审批', href: '/approvals' },
      { label: '技能注册表', href: '/skills' },
    ],
  },
]

export default function NavBarClient() {
  const [openTab, setOpenTab] = useState<string | null>(null)
  const navRef = useRef<HTMLDivElement>(null)
  const pathname = usePathname()

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenTab(null)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Close dropdown on route change
  useEffect(() => {
    setOpenTab(null)
  }, [pathname])

  // Find active tab from pathname
  const activeTab = TABS.find(t => t.items.some(i => {
    if (i.href === '/') return pathname === '/'
    return pathname.startsWith(i.href)
  }))

  return (
    <nav className="border-b border-[var(--card-border)] bg-[var(--card)] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4" ref={navRef}>
        {/* Top row: brand + tabs */}
        <div className="h-14 flex items-center justify-between">
          {/* Brand */}
          <a href="/" className="text-lg font-semibold text-white hover:text-blue-400 transition-colors whitespace-nowrap flex items-center gap-2">
            <span>🏢</span>
            <span className="hidden sm:inline">AI Company OS</span>
          </a>

          {/* Tabs */}
          <div className="flex items-center gap-1">
            {TABS.map(tab => {
              const isActive = activeTab?.id === tab.id
              const isOpen = openTab === tab.id
              return (
                <div key={tab.id} className="relative">
                  <button
                    onClick={() => setOpenTab(isOpen ? null : tab.id)}
                    className={`
                      flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors
                      ${isActive || isOpen
                        ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                        : 'text-[var(--muted)] hover:text-white hover:bg-zinc-800 border border-transparent'
                      }
                    `}
                  >
                    <span className="text-base">{tab.icon}</span>
                    <span className="hidden sm:inline">{tab.label}</span>
                    <svg
                      className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown */}
                  {isOpen && (
                    <div className="absolute top-full left-0 mt-1 w-44 bg-[var(--card)] border border-[var(--card-border)] rounded-lg shadow-xl py-1 z-50">
                      {tab.items.map(item => {
                        const isItemActive = item.href === '/'
                          ? pathname === '/'
                          : pathname.startsWith(item.href)
                        return (
                          <a
                            key={item.href}
                            href={item.href}
                            className={`
                              block px-4 py-2 text-sm transition-colors
                              ${isItemActive
                                ? 'text-blue-400 bg-blue-500/10'
                                : 'text-[var(--muted)] hover:text-white hover:bg-zinc-800'
                              }
                            `}
                          >
                            {item.label}
                          </a>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Version */}
          <div className="text-xs text-[var(--muted)] whitespace-nowrap">v0.25</div>
        </div>

        {/* Active tab indicator */}
        {activeTab && (
          <div className="text-xs text-[var(--muted)] pb-2 -mt-1 flex items-center gap-1.5">
            <span>{activeTab.icon}</span>
            <span>{activeTab.label}</span>
            <span className="text-[var(--card-border)]">/</span>
            <span className="text-[var(--foreground)]">
              {activeTab.items.find(i => {
                if (i.href === '/') return pathname === '/'
                return pathname.startsWith(i.href)
              })?.label || '...'}
            </span>
          </div>
        )}
      </div>
    </nav>
  )
}
