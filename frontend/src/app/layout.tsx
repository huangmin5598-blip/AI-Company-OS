import type { Metadata } from 'next'
import './globals.css'
import NavBarClient from '@/components/NavBarClient'

export const metadata: Metadata = {
  title: 'AI Company OS — Control Center',
  description: 'AI Company OS — 一人公司管理面板',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        <NavBarClient />
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  )
}
