'use client'

import { useEffect, useState } from 'react'
import { getLoopStats } from '@/lib/api'
import type { LoopStats } from '@/types/api'

function StatCard({ icon, label, value, bgColor }: { icon: string; label: string; value: string | number; bgColor?: string }) {
  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-[var(--muted)]">{label}</span>
      </div>
      <div className={`text-2xl font-semibold ${bgColor ? bgColor.replace('bg-', 'text-').replace('/10', '') : 'text-white'}`}>
        {value}
      </div>
    </div>
  )
}

function SimpleBarChart({ data, height = 160 }: { data: { date: string; count: number }[]; height?: number }) {
  const maxCount = Math.max(...data.map(d => d.count), 1)
  const barGap = 4
  const barWidth = Math.max(20, Math.min(50, (700 - data.length * barGap) / data.length))

  return (
    <div className="flex items-end gap-[4px] h-[160px]" style={{ height }}>
      {data.map((d, i) => {
        const barH = Math.max(4, (d.count / maxCount) * (height - 20))
        return (
          <div key={i} className="flex flex-col items-center justify-end flex-1 min-w-0">
            <div
              className="w-full bg-blue-500/60 hover:bg-blue-400 rounded-t transition-colors"
              style={{ height: barH }}
              title={`${d.date}: ${d.count} 个任务`}
            />
            <span className="text-[9px] text-[var(--muted)] mt-1 truncate w-full text-center">
              {d.date.slice(5)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function DistributionBar({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data)
  const total = entries.reduce((s, [_, v]) => s + v, 0) || 1
  const colors: Record<string, string> = {
    pass: 'bg-green-500/80',
    revision_required: 'bg-orange-500/80',
    blocked: 'bg-red-500/80',
  }
  const labels: Record<string, string> = {
    pass: '✅ 通过',
    revision_required: '🔄 需修改',
    blocked: '🚫 阻塞',
  }

  return (
    <div className="space-y-2">
      <div className="flex h-4 rounded overflow-hidden">
        {entries.map(([key, val]) => (
          <div
            key={key}
            className={`${colors[key] || 'bg-zinc-600'} transition-all`}
            style={{ width: `${(val / total) * 100}%` }}
            title={`${labels[key] || key}: ${val}`}
          />
        ))}
      </div>
      <div className="space-y-1">
        {entries.map(([key, val]) => (
          <div key={key} className="flex items-center justify-between text-xs">
            <span className="text-zinc-300">{labels[key] || key}</span>
            <span className="text-white">{val} ({((val / total) * 100).toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function LoopDashboardPage() {
  const [stats, setStats] = useState<LoopStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(false)

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const data = await getLoopStats()
      setStats(data)
    } catch (e) {
      setError('加载闭环统计数据失败')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh])

  if (loading && !stats) {
    return <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
  }

  if (error && !stats) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <div className="text-red-400">⚠️ {error}</div>
        <button onClick={loadData} className="px-4 py-2 bg-blue-600 rounded text-sm hover:bg-blue-700 transition-colors">
          重试
        </button>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">🔄 Loop Dashboard 闭环总览</h1>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-[var(--muted)] cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={e => setAutoRefresh(e.target.checked)}
              className="accent-blue-500"
            />
            自动刷新
          </label>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded text-xs text-white hover:bg-zinc-700 transition-colors disabled:opacity-50"
          >
            {loading ? '刷新中...' : '🔄 刷新'}
          </button>
        </div>
      </div>

      {/* Bottleneck alert */}
      {stats.pending_approval_tasks > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm text-yellow-400">
          ⚠️ 当前有 <strong>{stats.pending_approval_tasks}</strong> 个任务等待审批
        </div>
      )}
      {stats.pending_candidates > 0 && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-400">
          💡 当前有 <strong>{stats.pending_candidates}</strong> 个 Learning Candidate 待处理
        </div>
      )}
      {stats.pending_approval_tasks === 0 && stats.pending_candidates === 0 && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-sm text-green-400">
          ✅ 闭环健康，无积压项
        </div>
      )}

      {/* Stats Cards: 4 in a row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon="📋" label="总任务数" value={stats.total_tasks} />
        <StatCard
          icon="⏳"
          label="待审批"
          value={stats.pending_approval_tasks}
          bgColor={stats.pending_approval_tasks > 0 ? 'text-yellow-400' : 'text-white'}
        />
        <StatCard
          icon="✅"
          label="审批通过率"
          value={`${stats.approval_rate}%`}
          bgColor={stats.approval_rate > 50 ? 'text-green-400' : 'text-white'}
        />
        <StatCard
          icon="🧠"
          label="待处理候选"
          value={stats.pending_candidates}
          bgColor={stats.pending_candidates > 0 ? 'text-purple-400' : 'text-white'}
        />
      </div>

      {/* Distribution cards: 3 in a row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Review Distribution */}
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h3 className="text-sm font-medium text-[var(--muted)] mb-3">📊 Review 结果分布</h3>
          {Object.keys(stats.review_distribution).length > 0 ? (
            <DistributionBar data={stats.review_distribution} />
          ) : (
            <div className="text-xs text-[var(--muted)] text-center py-6">暂无数据</div>
          )}
        </div>

        {/* Alert Pooled */}
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h3 className="text-sm font-medium text-[var(--muted)] mb-3">🔔 Alert 入池</h3>
          <div className="text-3xl font-semibold text-white">{stats.alert_pooled_count}</div>
          <div className="text-xs text-[var(--muted)] mt-1">来自告警的任务数</div>
        </div>

        {/* Learning Candidates */}
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h3 className="text-sm font-medium text-[var(--muted)] mb-3">📈 Learning Candidate</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-semibold text-white">{stats.candidate_count}</span>
            <span className="text-sm text-[var(--muted)]">总候选</span>
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-semibold text-green-400">{stats.candidate_approved_count}</span>
            <span className="text-sm text-[var(--muted)]">已批准</span>
          </div>
        </div>
      </div>

      {/* Trend section */}
      {stats.recent_task_trend.length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h3 className="text-sm font-medium text-[var(--muted)] mb-3">📅 任务创建趋势</h3>
          <SimpleBarChart data={stats.recent_task_trend} height={160} />
          <div className="flex justify-between text-[10px] text-[var(--muted)] mt-1">
            <span>7天趋势</span>
            <span>峰值: {Math.max(...stats.recent_task_trend.map(d => d.count))}</span>
          </div>
        </div>
      )}
    </div>
  )
}
