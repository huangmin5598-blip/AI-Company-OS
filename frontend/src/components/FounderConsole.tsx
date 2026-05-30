'use client'

import { useEffect, useState } from 'react'

const FOUNDER_CONSOLE_API = '/api/v1/founder-console'

type Event = {
  id: string
  event_type: string
  source_id: string
  work_order_id: string
  decision_id: string
  draft_id: string
  asset_id: string
  timestamp: string
  summary: string
}

type Asset = {
  id: string
  asset_type: string
  path: string
  summary: string
  source_work_order: string
  source_decision: string
  created_at: string
}

type WOData = {
  total: number
  by_status: Record<string, number>
  recent_completed: { id: string; status: string; summary: string; completed_at: string }[]
}

type ConsoleData = {
  generated_at: string
  work_orders: WOData
  recent_events: Event[]
  recent_assets: Asset[]
  latest_brief: { path: string; filename: string; exists: boolean } | null
  decisions: { total: number; executed: number; pending: number }
  drafts: { total: number; pending: number; completed: number }
  capabilities: { agents: number; loaded: boolean; by_runtime?: Record<string, number> }
  health_summary: { checks: { name: string; status: string; action?: string }[]; pass_count: number; total: number }
  recommended_actions: { priority: string; message: string; command: string }[]
}

const STATUS_ICONS: Record<string, string> = {
  completed: '✅', failed: '❌', in_progress: '🔄', cancelled: '⏭️',
  needs_review: '⚠️', created: '📝', routed: '📎', assigned: '📌', blocked: '🔒',
}

export default function FounderConsole() {
  const [data, setData] = useState<ConsoleData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(FOUNDER_CONSOLE_API)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [])

  if (loading) return <div className="text-[var(--muted)] text-sm p-4">Loading Founder Console...</div>
  if (error) return <div className="text-red-400 text-sm p-4">Failed to load: {error}</div>
  if (!data) return null

  return (
    <div className="space-y-4 mb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">📊 Founder Console</h2>
        <span className="text-xs text-[var(--muted)]">Updated: {data.generated_at}</span>
      </div>

      {/* Health Summary */}
      <HealthCards checks={data.health_summary.checks} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Work Orders */}
        <MiniCard title="📋 Work Orders" icon="">
          <div className="text-2xl font-bold text-white mb-2">{data.work_orders.total}</div>
          <div className="space-y-1 text-xs">
            {Object.entries(data.work_orders.by_status).map(([s, c]) => (
              <div key={s} className="flex justify-between">
                <span className="text-[var(--muted)]">{STATUS_ICONS[s] || '•'} {s}</span>
                <span className="text-white">{c}</span>
              </div>
            ))}
          </div>
        </MiniCard>

        {/* Decisions & Drafts */}
        <MiniCard title="📋 Decisions & Drafts" icon="">
          <div className="space-y-3 text-sm mt-2">
            <div>
              <span className="text-[var(--muted)]">Decisions: </span>
              <span className="text-white">{data.decisions.total}</span>
              <span className="text-green-400 ml-2">✓{data.decisions.executed}</span>
              <span className="text-yellow-400 ml-2">⏳{data.decisions.pending}</span>
            </div>
            <div>
              <span className="text-[var(--muted)]">Drafts: </span>
              <span className="text-white">{data.drafts.total}</span>
              <span className="text-green-400 ml-2">✓{data.drafts.completed}</span>
              <span className="text-yellow-400 ml-2">⏳{data.drafts.pending}</span>
            </div>
          </div>
        </MiniCard>

        {/* Capabilities */}
        <MiniCard title="🧠 Capabilities" icon="">
          <div className="text-2xl font-bold text-white mb-2">{data.capabilities.agents}</div>
          <div className="space-y-1 text-xs">
            {data.capabilities.by_runtime && Object.entries(data.capabilities.by_runtime).map(([r, c]) => (
              <div key={r} className="flex justify-between">
                <span className="text-[var(--muted)]">{r}</span>
                <span className="text-white">{c} agents</span>
              </div>
            ))}
          </div>
        </MiniCard>

        {/* Assets */}
        <MiniCard title="📦 Assets" icon="">
          <div className="text-2xl font-bold text-white mb-2">{data.recent_assets.length}</div>
          <div className="space-y-1 text-xs max-h-32 overflow-y-auto">
            {data.recent_assets.map(a => (
              <div key={a.id} className="truncate">
                <span className="text-blue-400">[{a.asset_type}]</span>{' '}
                <span className="text-[var(--muted)]">{a.summary || a.path}</span>
              </div>
            ))}
          </div>
        </MiniCard>
      </div>

      {/* Recent Events */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <h3 className="text-sm font-medium text-white mb-3">📋 Recent Events</h3>
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {data.recent_events.map(e => (
            <div key={e.id} className="flex items-start gap-2 text-xs">
              <span className="text-blue-400 whitespace-nowrap">[{e.event_type}]</span>
              <span className="text-[var(--muted)] flex-1 truncate">{e.summary}</span>
              <span className="text-[var(--muted)] whitespace-nowrap">{e.timestamp.slice(5, 16)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Actions */}
      {data.recommended_actions.length > 0 && (
        <div className="bg-[var(--card)] border border-yellow-500/30 rounded-lg p-4">
          <h3 className="text-sm font-medium text-yellow-400 mb-3">⚠️ Recommended Actions</h3>
          <div className="space-y-2">
            {data.recommended_actions.map((a, i) => (
              <div key={i} className="text-xs">
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    a.priority === 'high' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                  }`}>{a.priority}</span>
                  <span className="text-[var(--muted)]">{a.message}</span>
                </div>
                <code className="block mt-1 text-[10px] bg-zinc-800 rounded px-2 py-1 text-blue-400">{a.command}</code>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MiniCard({ title, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
      <h3 className="text-sm font-medium text-white mb-2">{title}</h3>
      {children}
    </div>
  )
}

function HealthCards({ checks }: { checks: { name: string; status: string; action?: string }[] }) {
  const colors: Record<string, string> = {
    pass: 'bg-green-500/10 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    fail: 'bg-red-500/10 text-red-400 border-red-500/30',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  }
  const icons: Record<string, string> = {
    pass: '✅', warning: '⚠️', fail: '❌', info: 'ℹ️',
  }

  return (
    <div className="flex flex-wrap gap-2">
      {checks.map(c => (
        <div
          key={c.name}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border ${colors[c.status] || colors.info}`}
          title={c.action || c.name}
        >
          <span>{icons[c.status] || '•'}</span>
          <span>{c.name}</span>
          {c.action && (
            <span className="text-[10px] opacity-70 ml-1 cursor-help" title={c.action}>?</span>
          )}
        </div>
      ))}
    </div>
  )
}
