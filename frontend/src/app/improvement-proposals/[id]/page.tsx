'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getImprovementProposal, approveImprovementProposal, rejectImprovementProposal, closeImprovementProposal } from '@/lib/api'
import type { ImprovementProposal as ProposalType } from '@/types/api'

const STATUS_COLORS: Record<string, string> = {
  proposed: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  approved: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  action_created: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  closed_success: 'bg-green-500/10 text-green-400 border-green-500/30',
  closed_failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  rejected: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  dismissed: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
}

const PROPOSAL_LABELS: Record<string, string> = {
  retry_task_proposal: '🔄 重试任务',
  context_update_proposal: '📝 更新上下文',
  budget_review_proposal: '💰 预算审查',
  runtime_recovery_proposal: '⚙️ 运行时恢复',
  memory_update_proposal: '🧠 知识更新',
}

const PROPOSAL_TYPE_COLORS: Record<string, string> = {
  retry_task_proposal: 'bg-blue-500/10 text-blue-400',
  context_update_proposal: 'bg-purple-500/10 text-purple-400',
  budget_review_proposal: 'bg-yellow-500/10 text-yellow-400',
  runtime_recovery_proposal: 'bg-red-500/10 text-red-400',
  memory_update_proposal: 'bg-emerald-500/10 text-emerald-400',
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}

function ActionButton({ label, color, onClick, disabled }: {
  label: string; color: string; onClick: () => void; disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
        disabled ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed' : color
      }`}
    >
      {label}
    </button>
  )
}

export default function ProposalDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)
  const [proposal, setProposal] = useState<ProposalType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [founderNotes, setFounderNotes] = useState('')
  const [actionMsg, setActionMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getImprovementProposal(id)
      .then(setProposal)
      .catch(() => setError('无法加载提案'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[var(--muted)]">加载中...</div>
      </div>
    )
  }

  if (error || !proposal) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="text-red-400 text-lg">⚠️ {error || '提案不存在'}</div>
        <button onClick={() => router.back()} className="text-sm text-blue-400 hover:underline">
          ← 返回
        </button>
      </div>
    )
  }

  const handleApprove = async () => {
    try {
      const r = await approveImprovementProposal(id, founderNotes)
      setActionMsg(`✅ 已批准 — 创建 Task #${r.task_id}`)
      const updated = await getImprovementProposal(id)
      setProposal(updated)
    } catch { setActionMsg('❌ 批准失败') }
  }

  const handleReject = async () => {
    try {
      const r = await rejectImprovementProposal(id, founderNotes)
      setActionMsg(`✅ 已驳回`)
      const updated = await getImprovementProposal(id)
      setProposal(updated)
    } catch { setActionMsg('❌ 驳回失败') }
  }

  const handleCloseSuccess = async () => {
    try {
      const r = await closeImprovementProposal(id, 'success', {
        confirmed_by: 'founder', checked: true, timestamp: new Date().toISOString(),
      })
      setActionMsg(`✅ 已关闭 (成功)`)
      const updated = await getImprovementProposal(id)
      setProposal(updated)
    } catch { setActionMsg('❌ 关闭失败') }
  }

  const handleCloseFailed = async () => {
    try {
      const r = await closeImprovementProposal(id, 'failed', {
        reason: founderNotes || 'Manual verification failed',
      })
      setActionMsg(`✅ 已关闭 (失败)`)
      const updated = await getImprovementProposal(id)
      setProposal(updated)
    } catch { setActionMsg('❌ 关闭失败') }
  }

  const riskColor = proposal.risk_level === 'high' ? 'text-red-400' : proposal.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.push('/approvals')} className="text-sm text-[var(--muted)] hover:text-white">
          ← 回到审批
        </button>
      </div>

      {/* Title + Status */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-medium text-white">{proposal.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge status={proposal.status} />
            <span className={`px-2 py-0.5 rounded text-xs border ${PROPOSAL_TYPE_COLORS[proposal.proposal_type] || ''}`}>
              {PROPOSAL_LABELS[proposal.proposal_type] || proposal.proposal_type}
            </span>
            {proposal.requires_command_center && (
              <span className="px-2 py-0.5 rounded text-xs border bg-red-500/10 text-red-400 border-red-500/30">
                ⚡ 需 Command Center
              </span>
            )}
            <span className={`text-xs ${riskColor}`}>
              {proposal.risk_level.toUpperCase()} RISK
            </span>
          </div>
        </div>
      </div>

      {/* Summary + Rationale */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
        {proposal.rationale && (
          <div>
            <div className="text-xs text-[var(--muted)] mb-1">📋 理由</div>
            <div className="text-sm text-white/80">{proposal.rationale}</div>
          </div>
        )}

        <div className="flex gap-4 text-xs text-[var(--muted)]">
          <div>
            <span className="block text-xs mb-0.5">来源类型</span>
            <span className="text-white/70">{proposal.source_finding_type}</span>
          </div>
          {proposal.approval_id && (
            <div>
              <span className="block text-xs mb-0.5">审批 ID</span>
              <span className="text-white/70">#{proposal.approval_id}</span>
            </div>
          )}
          {proposal.created_task_id && (
            <div>
              <span className="block text-xs mb-0.5">关联任务</span>
              <span className="text-blue-400">#{proposal.created_task_id}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Plan */}
      {proposal.action_plan && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">📋 执行计划</h2>
          <div className="text-xs text-white/70 space-y-1">
            {((proposal.action_plan.steps || []) as unknown as string[]).map((step: string, i: number) => (
              <div key={i}>{step}</div>
            ))}
            {(proposal.action_plan.note as unknown as string) && (
              <div className="mt-2 text-yellow-400/70 italic">⚠️ {(proposal.action_plan.note as unknown as string)}</div>
            )}
          </div>
        </div>
      )}

      {/* Verification Plan */}
      {proposal.verification_plan && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">✅ 验证方案</h2>
          <div className="text-xs text-white/70 space-y-1">
            {((proposal.verification_plan.checks || []) as unknown as string[]).map((check: string, i: number) => (
              <div key={i}>• {check}</div>
            ))}
            <div className="mt-2 text-[var(--muted)]">预期: {(proposal.verification_plan.expected as unknown as string)}</div>
          </div>
        </div>
      )}

      {/* Verification Result (if closed) */}
      {proposal.verification_result && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">📊 验证结果</h2>
          <pre className="text-xs text-white/70 whitespace-pre-wrap">
            {JSON.stringify(proposal.verification_result, null, 2)}
          </pre>
          {proposal.verified_by && (
            <div className="text-xs text-[var(--muted)] mt-2">
              验证人: {proposal.verified_by} · {proposal.verified_at && new Date(proposal.verified_at).toLocaleString('zh-CN')}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {proposal.status === 'proposed' && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
          <h2 className="text-sm font-medium text-white">Actions</h2>
          <textarea
            value={founderNotes}
            onChange={e => setFounderNotes(e.target.value)}
            placeholder="审批备注（可选）"
            className="w-full p-2 bg-zinc-800 border border-[var(--card-border)] rounded text-sm text-white/80 placeholder:text-zinc-500 resize-none"
            rows={2}
          />
          <div className="flex gap-2">
            <ActionButton label="✅ 批准" color="bg-blue-600 text-white hover:bg-blue-700" onClick={handleApprove} />
            <ActionButton label="❌ 驳回" color="bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30" onClick={handleReject} />
          </div>
        </div>
      )}

      {proposal.status === 'action_created' && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
          <h2 className="text-sm font-medium text-white">确认结果</h2>
          <textarea
            value={founderNotes}
            onChange={e => setFounderNotes(e.target.value)}
            placeholder="验证备注（可选）"
            className="w-full p-2 bg-zinc-800 border border-[var(--card-border)] rounded text-sm text-white/80 placeholder:text-zinc-500 resize-none"
            rows={2}
          />
          <div className="flex gap-2">
            <ActionButton label="✅ 关闭 — 成功" color="bg-green-600 text-white hover:bg-green-700" onClick={handleCloseSuccess} />
            <ActionButton label="❌ 关闭 — 失败" color="bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30" onClick={handleCloseFailed} />
          </div>
        </div>
      )}

      {/* Action message */}
      {actionMsg && (
        <div className="text-sm text-center py-2 rounded bg-zinc-800/50 text-white">
          {actionMsg}
        </div>
      )}
    </div>
  )
}
