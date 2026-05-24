'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getImprovementProposals } from '@/lib/api'
import type { ImprovementProposal } from '@/types/api'

const STATUS_COLORS: Record<string, string> = {
  proposed: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  approved: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  action_created: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  closed_success: 'bg-green-500/10 text-green-400 border-green-500/30',
  closed_failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  rejected: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  dismissed: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
}

const PROPOSAL_TYPE_ICON: Record<string, string> = {
  retry_task_proposal: '🔄',
  context_update_proposal: '📝',
  budget_review_proposal: '💰',
  runtime_recovery_proposal: '⚙️',
  memory_update_proposal: '🧠',
}

const RISK_COLORS: Record<string, string> = {
  high: 'text-red-400',
  medium: 'text-yellow-400',
  low: 'text-green-400',
}

export default function ImprovementProposalsPage() {
  const router = useRouter()
  const [proposals, setProposals] = useState<ImprovementProposal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    getImprovementProposals(statusFilter || undefined)
      .then(setProposals)
      .catch(() => setError('无法加载改进提案'))
      .finally(() => setLoading(false))
  }, [statusFilter])

  const statusCounts: Record<string, number> = {}
  proposals.forEach(p => {
    statusCounts[p.status] = (statusCounts[p.status] || 0) + 1
  })

  const tabs = [
    { key: null, label: '全部', count: proposals.length },
    { key: 'proposed', label: '待审批', count: statusCounts.proposed || 0 },
    { key: 'action_created', label: '待执行', count: statusCounts.action_created || 0 },
    { key: 'closed_success', label: '已成功', count: statusCounts.closed_success || 0 },
    { key: 'closed_failed', label: '已失败', count: statusCounts.closed_failed || 0 },
    { key: 'rejected', label: '已驳回', count: statusCounts.rejected || 0 },
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
          💡 改进提案
          <span className="ml-2 text-sm text-[var(--muted)] font-normal">
            ({proposals.length} 条)
          </span>
        </h1>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: '待审批', count: statusCounts.proposed || 0, color: 'text-blue-400' },
          { label: '待执行', count: statusCounts.action_created || 0, color: 'text-indigo-400' },
          { label: '成功', count: statusCounts.closed_success || 0, color: 'text-green-400' },
          { label: '失败/驳回', count: (statusCounts.closed_failed || 0) + (statusCounts.rejected || 0), color: 'text-red-400' },
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

      {/* Proposal list */}
      {proposals.length === 0 ? (
        <div className="text-sm text-[var(--muted)] text-center py-16 border border-dashed border-zinc-700 rounded-lg">
          暂无改进提案
        </div>
      ) : (
        <div className="space-y-2">
          {proposals.map(p => (
            <div
              key={p.id}
              onClick={() => router.push(`/improvement-proposals/${p.id}`)}
              className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-3 hover:border-blue-500/40 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{PROPOSAL_TYPE_ICON[p.proposal_type] || '💡'}</span>
                    <span className="text-sm text-white truncate">{p.title}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] border ${STATUS_COLORS[p.status] || ''}`}>
                      {p.status.replace('_', ' ')}
                    </span>
                    <span className={`text-[10px] ${RISK_COLORS[p.risk_level] || 'text-zinc-400'}`}>
                      {p.risk_level.toUpperCase()}
                    </span>
                    {p.requires_command_center && (
                      <span className="text-[10px] text-red-400/70">⚡ Command Center</span>
                    )}
                    <span className="text-[10px] text-[var(--muted)]">
                      {p.created_at ? new Date(p.created_at).toLocaleDateString('zh-CN') : ''}
                    </span>
                  </div>
                </div>
                {p.verification_result && p.status === 'closed_success' && (
                  <span className="text-green-400 text-xs">✅</span>
                )}
                {p.status === 'closed_failed' && (
                  <span className="text-red-400 text-xs">❌</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
