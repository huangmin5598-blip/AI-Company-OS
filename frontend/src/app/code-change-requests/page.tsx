'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getCodeChangeRequests } from '@/lib/api'
import type { CodeChangeRequest, CodeChangeStatus } from '@/types/code-change'
import { STATUS_LABELS, STATUS_COLORS, STATUS_ORDER, RISK_COLORS } from '@/types/code-change'

function StatusBadge({ status }: { status: CodeChangeStatus }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
      {STATUS_LABELS[status] || status}
    </span>
  )
}

export default function CodeChangeRequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<CodeChangeRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    getCodeChangeRequests()
      .then(setRequests)
      .catch(() => setError('无法加载代码变更请求'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = statusFilter
    ? requests.filter(r => r.status === statusFilter)
    : requests

  const statusCounts: Record<string, number> = {}
  requests.forEach(r => {
    statusCounts[r.status] = (statusCounts[r.status] || 0) + 1
  })

  // Group tabs by phase
  const tabs = [
    { key: null, label: '全部', count: requests.length },
    { key: 'plan_generated', label: '待审批', count: statusCounts.plan_generated || 0 },
    { key: 'plan_approved', label: '待生成', count: statusCounts.plan_approved || 0 },
    { key: 'checks_passed', label: '待应用', count: statusCounts.checks_passed || 0 },
    { key: 'checks_warning', label: '告警', count: statusCounts.checks_warning || 0 },
    { key: 'checks_failed', label: '失败', count: statusCounts.checks_failed || 0 },
    { key: 'applied', label: '已应用', count: statusCounts.applied || 0 },
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
          🧬 代码桥
          <span className="ml-2 text-sm text-[var(--muted)] font-normal">
            ({requests.length} 条代码变更请求)
          </span>
        </h1>
        <a
          href="/execution-requests"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          ← 执行桥
        </a>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: '待处理', count: (statusCounts.plan_generated || 0) + (statusCounts.plan_approved || 0) + (statusCounts.checks_passed || 0), color: 'text-yellow-400' },
          { label: '已应用', count: statusCounts.applied || 0, color: 'text-green-400' },
          { label: '已回滚', count: statusCounts.rolled_back || 0, color: 'text-orange-400' },
          { label: '失败/拒绝', count: (statusCounts.checks_failed || 0) + (statusCounts.rejected || 0), color: 'text-red-400' },
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
      <div className="space-y-2">
        {filtered.length === 0 && (
          <div className="text-center text-[var(--muted)] py-12 text-sm">
            暂无代码变更请求
          </div>
        )}
        {filtered.map(r => (
          <div
            key={r.id}
            onClick={() => router.push(`/code-change-requests/${r.id}`)}
            className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 hover:bg-zinc-800/50 cursor-pointer transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-[var(--muted)] font-mono">#{r.id}</span>
                  <StatusBadge status={r.status} />
                  {r.applied_with_warning && (
                    <span className="text-[10px] bg-yellow-500/10 text-yellow-400 px-1.5 rounded border border-yellow-500/30">
                      ⚠️ 带警告应用
                    </span>
                  )}
                </div>
                <div className="text-sm text-white truncate">{r.title}</div>
                {r.plan_summary && (
                  <div className="text-xs text-[var(--muted)] mt-1 line-clamp-2">
                    {r.plan_summary}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-3 shrink-0 text-xs text-[var(--muted)]">
                {r.risk_level && (
                  <span className={RISK_COLORS[r.risk_level] || ''}>
                    {r.risk_level.toUpperCase()}
                  </span>
                )}
                {r.runtime_id && (
                  <span className="font-mono text-[10px]">{r.runtime_id}</span>
                )}
              </div>
            </div>

            {/* File list preview */}
            {r.files_expected.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {r.files_expected.map(f => (
                  <span key={f} className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
                    {f}
                  </span>
                ))}
              </div>
            )}

            {/* Audit trail */}
            <div className="flex items-center gap-3 mt-2 text-[10px] text-[var(--muted)]">
              {r.created_at && (
                <span>创建: {new Date(r.created_at).toLocaleString('zh-CN')}</span>
              )}
              {r.applied_at && (
                <span>应用: {new Date(r.applied_at).toLocaleString('zh-CN')}</span>
              )}
              {r.rolled_back_at && (
                <span>回滚: {new Date(r.rolled_back_at).toLocaleString('zh-CN')}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
