'use client'

import { useEffect, useState, useCallback } from 'react'
import { getApprovals, decideApproval, getTaskPoolItem } from '@/lib/api'
import type { ApprovalItem, TaskPoolItem } from '@/types/api'

const TARGET_ICON: Record<string, string> = {
  task: '📋',
  command: '⚡',
  learning_candidate: '🧠',
}

const RISK_ICON: Record<string, string> = {
  high: '🔴',
  medium: '🟡',
  low: '🟢',
}

const DECISION_COLORS: Record<string, string> = {
  approved: 'bg-green-500/20 text-green-400',
  revised: 'bg-orange-500/20 text-orange-400',
  rejected: 'bg-red-500/20 text-red-400',
  deferred: 'bg-yellow-500/20 text-yellow-400',
}

const DECISION_LABELS: Record<string, string> = {
  approved: '✅ 批准',
  revised: '✏️ 修改',
  rejected: '❌ 拒绝',
  deferred: '⏸️ 暂缓',
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [taskTitles, setTaskTitles] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'pending' | 'decided'>('pending')
  // Per-card note state: keyed by approval ID
  const [openNoteId, setOpenNoteId] = useState<number | null>(null)
  const [noteTexts, setNoteTexts] = useState<Record<number, string>>({})
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  const pendingApprovals = approvals.filter(a => a.status === 'approval_requested')
  const decidedApprovals = approvals.filter(a => a.status !== 'approval_requested')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getApprovals()
      setApprovals(data)
      const taskIds = [...new Set(data.filter(a => a.target_type === 'task').map(a => a.target_id))]
      const titles: Record<number, string> = {}
      await Promise.allSettled(
        taskIds.map(async id => {
          try {
            const t = await getTaskPoolItem(id)
            titles[id] = t.title
          } catch { /* ignore */ }
        })
      )
      setTaskTitles(prev => ({ ...prev, ...titles }))
    } catch (e) {
      setError('加载审批列表失败')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  async function handleDecision(approvalId: number, decision: string) {
    setActionLoading(approvalId)
    try {
      await decideApproval(approvalId, {
        founder_decision: decision,
        founder_notes: noteTexts[approvalId] || undefined,
      })
      // Clear note for this card
      setOpenNoteId(null)
      setNoteTexts(prev => {
        const next = { ...prev }
        delete next[approvalId]
        return next
      })
      await loadData()
    } catch (e) {
      console.error('Failed to decide approval', e)
    } finally {
      setActionLoading(null)
    }
  }

  function toggleNote(approvalId: number) {
    if (openNoteId === approvalId) {
      setOpenNoteId(null)
    } else {
      setOpenNoteId(approvalId)
      // Preserve existing note text if user already typed
      if (!noteTexts[approvalId]) {
        setNoteTexts(prev => ({ ...prev, [approvalId]: '' }))
      }
    }
  }

  function ApprovalCard({ a }: { a: ApprovalItem }) {
    const title = a.target_type === 'task' ? taskTitles[a.target_id] : null
    const isPending = a.status === 'approval_requested'
    const currentNote = noteTexts[a.id] ?? ''

    return (
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm">{TARGET_ICON[a.target_type] || '📋'}</span>
            <span className="text-xs font-medium text-white">
              {a.target_type}: #{a.target_id}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              a.risk_level === 'high' ? 'bg-red-500/20 text-red-400' :
              a.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-green-500/20 text-green-400'
            }`}>
              {RISK_ICON[a.risk_level] || '🟢'} {a.risk_level}
            </span>
          </div>
          {!isPending && a.founder_decision && (
            <span className={`text-[10px] px-2 py-0.5 rounded ${DECISION_COLORS[a.founder_decision] || 'bg-zinc-700 text-zinc-300'}`}>
              {a.founder_decision}
            </span>
          )}
        </div>

        {/* Title (if task) */}
        {title && (
          <div className="text-sm text-zinc-300 truncate" title={title}>
            {title}
          </div>
        )}

        {/* Reason */}
        {a.reason && (
          <div className="text-xs text-zinc-400">
            📝 {a.reason}
          </div>
        )}

        {/* Decision notes (for decided) */}
        {!isPending && a.founder_notes && (
          <div className="text-xs text-zinc-400 bg-zinc-800/50 rounded p-2">
            备注: {a.founder_notes}
          </div>
        )}

        {/* Timestamp */}
        <div className="text-[10px] text-[var(--muted)]">
          {a.created_at ? new Date(a.created_at).toLocaleString('zh-CN') : ''}
          {a.approved_at && ` · 处理: ${new Date(a.approved_at).toLocaleString('zh-CN')}`}
        </div>

        {/* Decision buttons (pending only) */}
        {isPending && (
          <div className="space-y-2 pt-1">
            {/* Notes textarea - shown when notes section is open */}
            {openNoteId === a.id && (
              <textarea
                key={`note-${a.id}`}
                placeholder="审批备注（可选）"
                value={currentNote}
                onChange={e => setNoteTexts(prev => ({ ...prev, [a.id]: e.target.value }))}
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-xs text-white resize-y min-h-[56px]"
              />
            )}
            <div className="flex flex-wrap gap-2">
              {(['approved', 'revised', 'rejected', 'deferred'] as const).map(decision => {
                const isActiveStep = openNoteId === a.id
                return (
                  <button
                    key={decision}
                    onClick={() => {
                      if (!isActiveStep) {
                        toggleNote(a.id)
                      } else {
                        handleDecision(a.id, decision)
                      }
                    }}
                    disabled={actionLoading === a.id}
                    className={`px-3 py-1.5 rounded text-xs transition-colors disabled:opacity-50 ${
                      decision === 'approved'
                        ? 'bg-green-600/20 border border-green-600/40 text-green-400 hover:bg-green-600/30'
                        : decision === 'revised'
                        ? 'bg-orange-600/20 border border-orange-600/40 text-orange-400 hover:bg-orange-600/30'
                        : decision === 'rejected'
                        ? 'bg-red-600/20 border border-red-600/40 text-red-400 hover:bg-red-600/30'
                        : 'bg-yellow-600/20 border border-yellow-600/40 text-yellow-400 hover:bg-yellow-600/30'
                    }`}
                  >
                    {isActiveStep ? `确认${DECISION_LABELS[decision].replace(/^.{1,2}\s/, '')}` : DECISION_LABELS[decision]}
                  </button>
                )
              })}
            </div>
            {openNoteId !== a.id && (
              <div className="text-[10px] text-[var(--muted)] pt-1">
                点击任一决策按钮可展开备注输入
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">
          ✅ Approval Center 审批中心
          {!loading && (
            <span className="ml-2 text-sm text-[var(--muted)] font-normal">
              ({pendingApprovals.length} 待审批)
            </span>
          )}
        </h1>
        <button
          onClick={loadData}
          className="text-xs text-[var(--muted)] hover:text-white transition-colors px-2 py-1"
          disabled={loading}
        >
          🔄 刷新
        </button>
      </div>

      {/* Cold-start guide banner */}
      {!loading && pendingApprovals.length > 0 && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-3 text-xs text-blue-300 space-y-1">
          <div className="font-medium">🧭 冷启动完成 — 建议走完一条完整闭环</div>
          <ol className="list-decimal list-inside space-y-0.5 text-blue-200/80">
            <li>✅ 审批通过一条任务</li>
            <li>⚡ 在指挥台执行已批准的任务</li>
            <li>📝 提交验收（Pass / Revision Required / Blocked）</li>
            <li>🧠 查看自动生成的 Learning Candidate</li>
          </ol>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--card-border)]">
        <button
          onClick={() => setTab('pending')}
          className={`px-4 py-2 text-sm transition-colors ${
            tab === 'pending'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-[var(--muted)] hover:text-white'
          }`}
        >
          ⏳ 待审批 ({pendingApprovals.length})
        </button>
        <button
          onClick={() => setTab('decided')}
          className={`px-4 py-2 text-sm transition-colors ${
            tab === 'decided'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-[var(--muted)] hover:text-white'
          }`}
        >
          ✅ 已决审批 ({decidedApprovals.length})
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
      ) : error ? (
        <div className="text-red-400 text-sm">⚠️ {error}</div>
      ) : (
        <div className="space-y-3">
          {(tab === 'pending' ? pendingApprovals : decidedApprovals).length === 0 ? (
            <div className="text-sm text-[var(--muted)] text-center py-16 border border-dashed border-zinc-700 rounded-lg">
              {tab === 'pending'
                ? '没有待审批项。系统正在监听新任务。'
                : '暂无已决审批记录。'}
            </div>
          ) : (
            (tab === 'pending' ? pendingApprovals : decidedApprovals).map(a => (
              <ApprovalCard key={a.id} a={a} />
            ))
          )}
        </div>
      )}
    </div>
  )
}
