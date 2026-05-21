'use client'

import { useEffect, useState } from 'react'
import { getAgents, getCosts } from '@/lib/api'
import type { Agent, CostSummary } from '@/types/api'

// Status badges for 3D agent state
function AgentStatusBadges({ agent }: { agent: Agent }) {
  const discoveryColors: Record<string, string> = {
    registered: 'bg-green-500/10 text-green-400 border-green-500/30',
    unregistered: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
    discovered: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  }
  const activityColors: Record<string, string> = {
    active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    inactive: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  }
  const healthColors: Record<string, string> = {
    ok: 'bg-green-500/10 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    error: 'bg-red-500/10 text-red-400 border-red-500/30',
  }

  return (
    <div className="flex flex-wrap gap-1 mt-1">
      <span className={`px-1.5 py-0.5 rounded text-[10px] border ${discoveryColors[agent.discovery_status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
        {agent.discovery_status}
      </span>
      <span className={`px-1.5 py-0.5 rounded text-[10px] border ${activityColors[agent.activity_status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
        {agent.activity_status}
      </span>
      <span className={`px-1.5 py-0.5 rounded text-[10px] border ${healthColors[agent.health_status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
        {agent.health_status}
      </span>
    </div>
  )
}

function AgentCard({ agent, costUsd }: { agent: Agent; costUsd: number }) {
  const statusColors: Record<string, string> = {
    online: 'bg-green-400',
    busy: 'bg-yellow-400',
    offline: 'bg-gray-400',
    error: 'bg-red-400',
  }
  const statusLabels: Record<string, string> = {
    online: '在线',
    busy: '忙碌',
    offline: '离线',
    error: '报错',
  }

  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 hover:border-blue-500/40 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-medium text-white">{agent.name}</h3>
          <div className="text-xs text-[var(--muted)] mt-0.5">{agent.identity || '-'}</div>
          <AgentStatusBadges agent={agent} />
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`inline-block w-2 h-2 rounded-full ${statusColors[agent.status] || 'bg-gray-400'}`} />
          <span className="text-xs text-[var(--muted)]">{statusLabels[agent.status] || agent.status}</span>
        </div>
      </div>

      <div className="text-xs text-[var(--muted)] space-y-1.5">
        <div className="flex justify-between">
          <span>🧠 模型</span>
          <span className="text-white/70">{agent.model || '-'}</span>
        </div>
        <div className="flex justify-between">
          <span>🎯 角色</span>
          <span className="text-white/70">{agent.role || agent.agent_type || 'openclaw'}</span>
        </div>
        <div className="flex justify-between">
          <span>💵 总成本</span>
          <span className="text-white/70">${costUsd.toFixed(6)}</span>
        </div>
        <div className="flex justify-between">
          <span>📊 执行次数</span>
          <span className="text-white/70">{agent.total_runs}</span>
        </div>
        <div className="flex justify-between">
          <span>📅 最近活跃</span>
          <span className="text-white/70">{agent.last_active_at?.split('T')[0] || '-'}</span>
        </div>
      </div>

      {agent.workspace && (
        <div className="mt-2 pt-2 border-t border-[var(--card-border)]">
          <div className="text-xs text-[var(--muted)] truncate" title={agent.workspace}>
            📂 {agent.workspace.replace(/^~\//, '~/')}
          </div>
        </div>
      )}

      {agent.recent_task && (
        <div className="mt-1 text-xs text-blue-400/70 truncate">
          🎯 {agent.recent_task}
        </div>
      )}
    </div>
  )
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const a = await getAgents()
        setAgents(a)
        setError(null)
      } catch (e) {
        setError('无法连接后端')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Cost data per agent from costs API
  const [costMap, setCostMap] = useState<Record<string, number>>({})
  useEffect(() => {
    getCosts('agent').then(c => {
      const map: Record<string, number> = {}
      c.items.forEach(i => { map[i.name] = i.total_cost_usd })
      setCostMap(map)
    }).catch(() => {})
  }, [])

  const filtered = filter === 'all'
    ? agents
    : agents.filter(a => a.status === filter)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[var(--muted)]">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="text-red-400 text-lg">⚠️ {error}</div>
      </div>
    )
  }

  const counts = {
    all: agents.length,
    online: agents.filter(a => a.status === 'online').length,
    busy: agents.filter(a => a.status === 'busy').length,
    offline: agents.filter(a => a.status === 'offline').length,
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium text-white">Agent 列表</h1>
        <div className="text-xs text-[var(--muted)]">共 {agents.length} 个 Agent</div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 text-sm">
        {[
          { key: 'all', label: `全部 (${counts.all})` },
          { key: 'online', label: `🟢 在线 (${counts.online})` },
          { key: 'busy', label: `🟡 忙碌 (${counts.busy})` },
          { key: 'offline', label: `🔴 离线 (${counts.offline})` },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setFilter(t.key)}
            className={`px-3 py-1.5 rounded text-xs transition-colors ${
              filter === t.key
                ? 'bg-blue-600 text-white'
                : 'bg-zinc-800 text-[var(--muted)] hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {filtered.map(agent => (
          <AgentCard key={agent.id} agent={agent} costUsd={costMap[agent.id] || 0} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center text-[var(--muted)] py-12">没有符合条件的 Agent</div>
      )}
    </div>
  )
}
