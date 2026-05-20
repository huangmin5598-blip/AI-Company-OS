'use client'

import { useEffect, useState } from 'react'
import { getStats, getBusinessLines, getAlerts, getRuns, getCosts } from '@/lib/api'
import type { Stats, BusinessLine, Alert, ExecutionRecord, CostSummary } from '@/types/api'

function StatusDot({ color }: { color: string }) {
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${color} mr-1.5`} />
}

function AlertBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    error: 'bg-red-500/10 text-red-400 border-red-500/30',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    critical: 'bg-red-600/20 text-red-300 border-red-600/40',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${colors[severity] || colors.info}`}>
      {severity}
    </span>
  )
}

function BusinessLineCard({ line }: { line: BusinessLine }) {
  const statusColors: Record<string, string> = {
    guaranteed: 'text-green-400',
    running: 'text-blue-400',
    error: 'text-red-400',
    scaffolded: 'text-yellow-400',
    paused: 'text-gray-400',
  }
  const statusDots: Record<string, string> = {
    guaranteed: 'bg-green-400',
    running: 'bg-blue-400',
    error: 'bg-red-400',
    scaffolded: 'bg-yellow-400',
    paused: 'bg-gray-400',
  }

  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 hover:border-blue-500/40 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-white">{line.name}</h3>
        <span className={`text-xs font-medium ${statusColors[line.status] || 'text-gray-400'}`}>
          <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusDots[line.status] || 'bg-gray-400'} mr-1`} />
          {line.status}
        </span>
      </div>
      <div className="text-xs text-[var(--muted)] space-y-1">
        <div className="flex justify-between">
          <span>运行次数</span>
          <span className="text-white">{line.total_runs}</span>
        </div>
        <div className="flex justify-between">
          <span>失败次数</span>
          <span className={line.failed_runs > 0 ? 'text-red-400' : 'text-white'}>{line.failed_runs}</span>
        </div>
        <div className="flex justify-between">
          <span>总成本</span>
          <span className="text-white">${line.total_cost_usd.toFixed(6)}</span>
        </div>
        {line.last_run_date && (
          <div className="flex justify-between">
            <span>最近运行</span>
            <span className="text-white">{line.last_run_date}</span>
          </div>
        )}
      </div>
      {line.recent_artifacts.length > 0 && (
        <div className="mt-2 pt-2 border-t border-[var(--card-border)]">
          <div className="text-xs text-[var(--muted)] mb-1">最近产出</div>
          {line.recent_artifacts.slice(0, 2).map((a, i) => (
            <div key={i} className="text-xs text-white/70 truncate">📄 {a}</div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [lines, setLines] = useState<BusinessLine[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [recentRuns, setRecentRuns] = useState<ExecutionRecord[]>([])
  const [costs, setCosts] = useState<CostSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  async function loadData() {
    try {
      const [s, l, a, r, c] = await Promise.all([
        getStats(), getBusinessLines(), getAlerts(),
        getRuns({ limit: 8 }), getCosts('model'),
      ])
      setStats(s); setLines(l); setAlerts(a)
      setRecentRuns(r); setCosts(c)
      setError(null)
    } catch (e) {
      setError('无法连接到后端，请确认 API 服务已启动')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  async function handleRefresh() {
    setRefreshing(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'}/api/v1/refresh`, { method: 'POST' })
      if (res.ok) await loadData()
    } catch { /* ignore */ }
    setRefreshing(false)
  }

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
        <button onClick={loadData} className="px-4 py-2 bg-blue-600 rounded text-sm hover:bg-blue-700 transition-colors">
          重试
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Status Bar */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-[var(--muted)]">系统概览</h2>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-xs px-3 py-1 bg-zinc-800 rounded hover:bg-zinc-700 transition-colors disabled:opacity-50"
          >
            {refreshing ? '刷新中...' : '🔄 刷新数据'}
          </button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatBox icon="🟢" label="Agent 在线" value={stats?.online_agents ?? 0} />
          <StatBox icon="🔴" label="离线" value={stats?.offline_agents ?? 0} color="text-red-400" />
          <StatBox icon="📋" label="业务线" value={stats?.business_line_count ?? 0} />
          <StatBox icon="⚠️" label="报错" value={stats?.error_lines ?? 0} color="text-red-400" />
          <StatBox icon="💰" label="月度成本" value={`$${(stats?.month_cost_usd ?? 0).toFixed(6)}`} />
          <StatBox icon="📊" label="总执行" value={stats?.total_executions ?? 0} />
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
          <h2 className="text-sm font-medium text-red-400 mb-3">⚠️ 需要关注</h2>
          <div className="space-y-2">
            {alerts.map(a => (
              <div key={a.id} className="flex items-start gap-3 text-sm">
                <AlertBadge severity={a.severity || 'info'} />
                <div>
                  <div className="text-white">{a.title}</div>
                  {a.description && <div className="text-xs text-[var(--muted)] mt-0.5">{a.description}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Business Line Cards */}
      <div>
        <h2 className="text-sm font-medium text-[var(--muted)] mb-3">业务线</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {lines.map(line => (
            <BusinessLineCard key={line.id} line={line} />
          ))}
        </div>
      </div>

      {/* Recent Runs */}
      <div>
        <h2 className="text-sm font-medium text-[var(--muted)] mb-3">最近执行记录</h2>
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--card-border)] text-[var(--muted)]">
                <th className="text-left p-3 font-medium">日期</th>
                <th className="text-left p-3 font-medium">业务线</th>
                <th className="text-left p-3 font-medium">任务</th>
                <th className="text-right p-3 font-medium">字数</th>
                <th className="text-center p-3 font-medium">结果</th>
                <th className="text-right p-3 font-medium">成本</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map(r => (
                <tr key={r.id} className="border-b border-[var(--card-border)] last:border-0 hover:bg-zinc-800/50">
                  <td className="p-3 text-white/80">{r.date}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs">{r.business_line}</span>
                  </td>
                  <td className="p-3 text-white/80 truncate max-w-[200px]">{r.title || r.task_id}</td>
                  <td className="p-3 text-right text-white/80">{r.word_count > 0 ? r.word_count.toLocaleString() : '-'}</td>
                  <td className="p-3 text-center">
                    {r.result === 'passed' ? (
                      <span className="text-green-400">✅</span>
                    ) : r.result === 'failed' ? (
                      <span className="text-red-400" title={r.result_detail || ''}>❌</span>
                    ) : (
                      <span className="text-yellow-400">⏳</span>
                    )}
                  </td>
                  <td className="p-3 text-right text-white/80">${r.cost_usd.toFixed(6)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-2 text-right">
          <a href="/runs" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
            查看全部执行记录 →
          </a>
        </div>
      </div>
    </div>
  )
}

function StatBox({ icon, label, value, color }: { icon: string; label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-zinc-800/50 rounded p-3">
      <div className="text-xs text-[var(--muted)] mb-1">{icon} {label}</div>
      <div className={`text-xl font-semibold ${color || 'text-white'}`}>{value}</div>
    </div>
  )
}
