import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Company Control Center',
  description: 'AI Company OS — 一人公司管理面板',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        <NavBar />
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  )
}

function NavBar() {
  return (
    <nav className="border-b border-[var(--card-border)] bg-[var(--card)]">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <a href="/" className="text-lg font-semibold text-white hover:text-blue-400 transition-colors">
            🏢 AI Company Control Center
          </a>
          <div className="hidden sm:flex items-center gap-4 text-sm">
            <NavLink href="/" label="总览" />
            <NavLink href="/agents" label="Agent" />
            <NavLink href="/runs" label="执行记录" />
            <NavLink href="/command" label="指挥台" />
            <NavLink href="/tasks" label="任务看板" />
            <NavLink href="/skills" label="技能地图" />
            <NavLink href="/analysis" label="分析" />
          </div>
        </div>
        <div className="text-xs text-[var(--muted)]">v0.3</div>
      </div>
    </nav>
  )
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="text-[var(--muted)] hover:text-white transition-colors px-2 py-1 rounded hover:bg-zinc-800"
    >
      {label}
    </a>
  )
}
