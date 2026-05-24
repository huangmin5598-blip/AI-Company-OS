'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  getExecutionRequest,
  dryRunExecutionRequest,
  confirmExecutionRequest,
  executeExecutionRequest,
  verifyExecutionRequest,
  cancelExecutionRequest,
} from '@/lib/api'
import type { ExecutionRequest as ExecutionRequestType, ExecutionRequestStatus } from '@/types/execution'
import {
  STATUS_LABELS,
  STATUS_COLORS,
  ACTION_TYPE_LABELS,
  ACTION_TYPE_COLORS,
} from '@/types/execution'

function StatusBadge({ status }: { status: ExecutionRequestStatus }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
      {STATUS_LABELS[status] || status.replace('_', ' ')}
    </span>
  )
}

function ActionButton({ label, color, onClick, disabled, loading }: {
  label: string; color?: string; onClick: () => void; disabled?: boolean; loading?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
        disabled || loading ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed' : (color || 'bg-blue-600 text-white hover:bg-blue-700')
      }`}
    >
      {loading ? '处理中...' : label}
    </button>
  )
}

/** Step in the execution state machine */
function StepIndicator({ label, done, active, index }: { label: string; done: boolean; active: boolean; index: number }) {
  return (
    <div className={`flex items-center gap-2 ${active ? 'text-white' : done ? 'text-green-400' : 'text-zinc-600'}`}>
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium border ${
        done ? 'bg-green-500/20 border-green-500/50' :
        active ? 'bg-blue-600 border-blue-500' :
        'bg-zinc-800 border-zinc-700'
      }`}>
        {done ? '✓' : index}
      </div>
      <span className="text-xs">{label}</span>
    </div>
  )
}

export default function ExecutionRequestDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)
  const [request, setRequest] = useState<ExecutionRequestType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [founderNote, setFounderNote] = useState('')

  const load = () => {
    if (!id) return
    getExecutionRequest(id)
      .then(setRequest)
      .catch(() => setError('无法加载执行请求'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[var(--muted)]">加载中...</div>
      </div>
    )
  }

  if (error || !request) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="text-red-400 text-lg">⚠️ {error || '请求不存在'}</div>
        <button onClick={() => router.back()} className="text-sm text-blue-400 hover:underline">← 返回</button>
      </div>
    )
  }

  const handleAction = async (action: string, fn: () => Promise<any>) => {
    setActionLoading(action)
    setActionMsg(null)
    try {
      const r = await fn()
      if (action === 'dry-run') setActionMsg('✅ Dry-Run 完成')
      else if (action === 'confirm') setActionMsg(`✅ 已确认执行 — ${r.status}`)
      else if (action === 'execute') setActionMsg('✅ 已执行')
      else if (action === 'verify') setActionMsg(`✅ 验证完成 — ${r.status}`)
      else if (action === 'cancel') setActionMsg('✅ 已取消')
      await load()
    } catch (e: any) {
      setActionMsg(`❌ 操作失败: ${e.message || '未知错误'}`)
    } finally {
      setActionLoading(null)
    }
  }

  const riskColor = request.risk_level === 'high' ? 'text-red-400' : request.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'

  // ── State machine steps ──
  const steps = [
    { label: '确认执行', done: ['approved_for_execute', 'executed', 'verified_success', 'verified_failed'].includes(request.status), active: request.status === 'pending_confirmation' || request.status === 'dry_run_completed' },
    { label: '执行', done: ['executed', 'verified_success', 'verified_failed'].includes(request.status), active: request.status === 'approved_for_execute' },
    { label: '验证', done: ['verified_success', 'verified_failed'].includes(request.status), active: request.status === 'executed' },
    { label: '完成', done: ['verified_success', 'verified_failed'].includes(request.status), active: false },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back link */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.push('/execution-requests')} className="text-sm text-[var(--muted)] hover:text-white">
          ← 回到执行桥
        </button>
      </div>

      {/* Title + Status */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-medium text-white">
            {ACTION_TYPE_LABELS[request.action_type] || '⚙️ ' + request.action_type}
          </h1>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <StatusBadge status={request.status as ExecutionRequestStatus} />
            <span className={`px-2 py-0.5 rounded text-xs border ${ACTION_TYPE_COLORS[request.action_type] || ''}`}>
              {ACTION_TYPE_LABELS[request.action_type] || request.action_type}
            </span>
            <span className={`text-xs ${riskColor}`}>
              {request.risk_level.toUpperCase()} RISK
            </span>
            {request.dry_run_required && (
              <span className="px-2 py-0.5 rounded text-xs border bg-yellow-500/10 text-yellow-400 border-yellow-500/30">
                ⚡ 需 Dry-Run
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Linked entities */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <h2 className="text-sm font-medium text-white mb-2">🔗 关联</h2>
        <div className="flex gap-4 text-xs">
          <div>
            <span className="block text-[var(--muted)] mb-0.5">来源</span>
            <span className="text-white/70">{request.source_type}</span>
          </div>
          {request.proposal_id && (
            <div>
              <span className="block text-[var(--muted)] mb-0.5">改进提案</span>
              <a
                href={`/improvement-proposals/${request.proposal_id}`}
                className="text-blue-400 hover:underline"
                onClick={e => e.stopPropagation()}
              >
                #{request.proposal_id}
              </a>
            </div>
          )}
          {request.task_id && (
            <div>
              <span className="block text-[var(--muted)] mb-0.5">关联任务</span>
              <span className="text-white/70">#{request.task_id}</span>
            </div>
          )}
          {request.runtime_id && (
            <div>
              <span className="block text-[var(--muted)] mb-0.5">运行时</span>
              <span className="text-white/70">{request.runtime_id}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action payload */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <h2 className="text-sm font-medium text-white mb-2">📋 执行负载</h2>
        <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono">
          {JSON.stringify(request.action_payload, null, 2)}
        </pre>
      </div>

      {/* Dry-Run result (if completed) */}
      {request.dry_run_result && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">🔮 Dry-Run 预览</h2>
          <div className="text-xs text-white/70 space-y-2">
            {(request.dry_run_result.preview as string) && (
              <div className="whitespace-pre-wrap">{request.dry_run_result.preview as string}</div>
            )}
            {(request.dry_run_result.checklist as string[])?.length > 0 && (
              <div className="mt-2">
                <div className="text-[var(--muted)] mb-1">检查清单:</div>
                {(request.dry_run_result.checklist as string[]).map((c: string, i: number) => (
                  <div key={i}>• {c}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Execution result */}
      {request.execution_result && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">⚡ 执行结果</h2>
          <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono">
            {JSON.stringify(request.execution_result, null, 2)}
          </pre>
        </div>
      )}

      {/* Verification result */}
      {request.verification_result && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
          <h2 className="text-sm font-medium text-white mb-2">✅ 验证结果</h2>
          <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono">
            {JSON.stringify(request.verification_result, null, 2)}
          </pre>
          {request.verified_by && (
            <div className="text-xs text-[var(--muted)] mt-2">
              验证人: {request.verified_by} · {request.verified_at && new Date(request.verified_at).toLocaleString('zh-CN')}
            </div>
          )}
        </div>
      )}

      {/* State machine progress */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <h2 className="text-sm font-medium text-white mb-3">📌 执行流程</h2>
        <div className="flex items-center gap-4 justify-center">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-4">
              <StepIndicator label={s.label} done={s.done} active={s.active} index={i + 1} />
              {i < steps.length - 1 && (
                <div className={`w-6 h-px ${s.done ? 'bg-green-500/50' : 'bg-zinc-700'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Audit trail */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
        <h2 className="text-sm font-medium text-white mb-2">📜 审计记录</h2>
        <div className="text-xs text-[var(--muted)] space-y-1">
          {request.execute_confirmed_by && (
            <div>确认人: {request.execute_confirmed_by} · {request.execute_confirmed_at && new Date(request.execute_confirmed_at).toLocaleString('zh-CN')}</div>
          )}
          {request.execute_confirmation_note && (
            <div>确认备注: {request.execute_confirmation_note}</div>
          )}
          {request.executed_at && <div>执行时间: {new Date(request.executed_at).toLocaleString('zh-CN')}</div>}
          {request.verified_by && <div>验证人: {request.verified_by} · {request.verified_at && new Date(request.verified_at).toLocaleString('zh-CN')}</div>}
          {request.created_at && <div>创建时间: {new Date(request.created_at).toLocaleString('zh-CN')}</div>}
        </div>
      </div>

      {/* ── Action buttons by status ── */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-medium text-white">操作</h2>

        {/* pending_confirmation — dry-run (if needed) then confirm */}
        {(request.status === 'pending_confirmation' || request.status === 'dry_run_completed') && (
          <>
            <textarea
              value={founderNote}
              onChange={e => setFounderNote(e.target.value)}
              placeholder="确认备注（可选）"
              className="w-full p-2 bg-zinc-800 border border-[var(--card-border)] rounded text-sm text-white/80 placeholder:text-zinc-500 resize-none"
              rows={2}
            />
            <div className="flex gap-2 flex-wrap">
              {request.dry_run_required && request.status !== 'dry_run_completed' && (
                <ActionButton
                  label="🔮 Dry-Run"
                  onClick={() => handleAction('dry-run', () => dryRunExecutionRequest(id))}
                  loading={actionLoading === 'dry-run'}
                />
              )}
              <ActionButton
                label="✅ 确认执行"
                color="bg-blue-600 text-white hover:bg-blue-700"
                onClick={() => handleAction('confirm', () => confirmExecutionRequest(id, { confirmed_by: 'founder', note: founderNote }))}
                disabled={actionLoading !== null}
                loading={actionLoading === 'confirm'}
              />
              <ActionButton
                label="❌ 取消"
                color="bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
                onClick={() => handleAction('cancel', () => cancelExecutionRequest(id))}
                disabled={actionLoading !== null}
                loading={actionLoading === 'cancel'}
              />
            </div>
          </>
        )}

        {/* approved_for_execute — execute */}
        {request.status === 'approved_for_execute' && (
          <div className="flex gap-2">
            <ActionButton
              label="⚡ 执行"
              color="bg-green-600 text-white hover:bg-green-700"
              onClick={() => handleAction('execute', () => executeExecutionRequest(id))}
              disabled={actionLoading !== null}
              loading={actionLoading === 'execute'}
            />
            <ActionButton
              label="❌ 取消"
              color="bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
              onClick={() => handleAction('cancel', () => cancelExecutionRequest(id))}
              disabled={actionLoading !== null}
              loading={actionLoading === 'cancel'}
            />
          </div>
        )}

        {/* executed — verify */}
        {request.status === 'executed' && (
          <div className="flex gap-2">
            <ActionButton
              label="✅ 验证"
              color="bg-purple-600 text-white hover:bg-purple-700"
              onClick={() => handleAction('verify', () => verifyExecutionRequest(id))}
              disabled={actionLoading !== null}
              loading={actionLoading === 'verify'}
            />
          </div>
        )}

        {/* verified_success / verified_failed / cancelled — no actions */}
        {(request.status === 'verified_success' || request.status === 'verified_failed') && (
          <div className="text-xs text-[var(--muted)]">
            该执行请求已完成
          </div>
        )}
        {request.status === 'cancelled' && (
          <div className="text-xs text-[var(--muted)]">
            该执行请求已取消
          </div>
        )}
      </div>

      {/* Action message */}
      {actionMsg && (
        <div className={`text-sm text-center py-2 rounded bg-zinc-800/50 ${actionMsg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>
          {actionMsg}
        </div>
      )}
    </div>
  )
}
