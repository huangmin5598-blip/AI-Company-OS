'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getExecutionRequests } from '@/lib/api'
import type { ExecutionRequest } from '@/types/execution'
import { STATUS_LABELS, STATUS_COLORS, ACTION_TYPE_LABELS, ACTION_TYPE_COLORS } from '@/types/execution'

const RISK_COLORS: Record<string, string> = {
  high: 'text-red-400',
  medium: 'text-yellow-400',
  low: 'text-green-400',
}

const STATUS_ORDER = [
  'pending_confirmation',
  'dry_run_completed',
  'approved_for_execute',
  'executed',
  'verification_pending',
  'verified_success',
  'verified_failed',
  'cancelled',
]

export default function ExecutionRequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<ExecutionRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    getExecutionRequests(statusFilter || undefined)
      .then(setRequests)
      .catch(() => setError('无法加载执行请求'))
      .finally(() => setLoading(false))
  }, [statusFilter])

  const statusCounts: Record<string, number> = {}
  requests.forEach(r => {
    statusCounts[r.status] = (statusCounts[r.status] || 0) + 1
  })

  const tabs = [
    { key: null, label: '全部', count: requests.length },
    { key: 'pending_confirmation', label: '待确认', count: statusCounts.pending_confirmation || 0 },
    { key: 'approved_for_execute', label: '待执行', count: statusCounts.approved_for_execute || 0 },
    { key: 'verified_success', label: '成功', count: statusCounts.verified_success || 0 },
    { key: 'verified_failed', label: '失败', count: statusCounts.verified_failed || 0 },
    { key: 'cancelled', label: '已取消', count: statusCounts.cancelled || 0 },
  ]

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

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium text-white">
          🎯 执行桥
          <span className="ml-2 text-sm text-[var(--muted)] font-normal">
            ({requests.length} 条执行请求)
          </span>
        </h1>
        <a
          href="/improvement-proposals"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          ← 改进提案
        </a>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: '待确认', count: statusCounts.pending_confirmation || 0, color: 'text-yellow-400' },
          { label: '待执行', count: statusCounts.approved_for_execute || 0, color: 'text-indigo-400' },
          { label: '成功', count: statusCounts.verified_success || 0, color: 'text-green-400' },
          { label: '失败/取消', count: (statusCounts.verified_failed || 0) + (statusCounts.cancelled || 0), color: 'text-red-400' },
        ].map(s => (
          <div key={s.label} className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-3 text-center">
            <div className={`text-lg font-bold ${s.color}`}>{s.count}</div>
            <div className="text-[10px] text-[var(--muted)] mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {tabs.filter(t => t.count > 0 || t.key === null).map(t => (
          <button
            key={t.key || 'all'}
            onClick={() => setStatusFilter(t.key)}
            className={`px-3 py-1.5 rounded text-xs whitespace-nowrap transition-colors ${
              statusFilter === t.key
                ? 'bg-blue-600 text-white'
                : 'bg-zinc-800 text-[var(--muted)] hover:text-white'
            }`}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {/* Request list */}
      {requests.length === 0 ? (
        <div className="text-sm text-[var(--muted)] text-center py-16 border border-dashed border-zinc-700 rounded-lg">
          暂无执行请求
        </div>
      ) : (
        <div className="space-y-2">
          {requests.map(r => (
            <div
              key={r.id}
              onClick={() => router.push(`/execution-requests/${r.id}`)}
              className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-3 hover:border-blue-500/40 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{ACTION_TYPE_LABELS[r.action_type] || '⚙️ ' + r.action_type}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] border ${STATUS_COLORS[r.status as keyof typeof STATUS_COLORS] || ''}`}>
                      {STATUS_LABELS[r.status as keyof typeof STATUS_LABELS] || r.status}
                    </span>
                    <span className={`text-[10px] ${RISK_COLORS[r.risk_level] || 'text-zinc-400'}`}>
                      {r.risk_level.toUpperCase()}
                    </span>
                    {r.proposal_id && (
                      <span className="text-[10px] text-blue-400/70">提案 #{r.proposal_id}</span>
                    )}
                    {r.task_id && (
                      <span className="text-[10px] text-zinc-400">任务 #{r.task_id}</span>
                    )}
                    {r.dry_run_required && (
                      <span className="text-[10px] text-yellow-400/70">⚡ 需 Dry-Run</span>
                    )}
                    <span className="text-[10px] text-[var(--muted)]">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString('zh-CN') : ''}
                    </span>
                  </div>
                </div>
                {r.status === 'verified_success' && (
                  <span className="text-green-400 text-xs">✅</span>
                )}
                {r.status === 'verified_failed' && (
                  <span className="text-red-400 text-xs">❌</span>
                )}
                {r.status === 'cancelled' && (
                  <span className="text-zinc-500 text-xs">✕</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
