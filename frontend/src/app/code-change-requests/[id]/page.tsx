'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  getCodeChangeRequest,
  generatePlan as apiGeneratePlan,
  approvePlan as apiApprovePlan,
  generatePatch as apiGeneratePatch,
  runChecks as apiRunChecks,
  applyCodeChange as apiApplyCodeChange,
  rollbackCodeChange as apiRollbackCodeChange,
  rejectCodeChange as apiRejectCodeChange,
  reviseCodeChange as apiReviseCodeChange,
} from '@/lib/api'
import type { CodeChangeRequest as CCR, CodeChangeStatus, CheckItem } from '@/types/code-change'
import { STATUS_LABELS, STATUS_COLORS, RISK_COLORS } from '@/types/code-change'

// ── Mini components ──

function StatusBadge({ status }: { status: CodeChangeStatus }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[status] || 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30'}`}>
      {STATUS_LABELS[status] || status.replace('_', ' ')}
    </span>
  )
}

function ActionButton({ label, color, onClick, disabled, loading, variant }: {
  label: string; color?: string; onClick: () => void; disabled?: boolean; loading?: boolean; variant?: 'danger' | 'warning' | 'default'
}) {
  const baseColor = variant === 'danger'
    ? 'bg-red-600 text-white hover:bg-red-700'
    : variant === 'warning'
    ? 'bg-yellow-600 text-white hover:bg-yellow-700'
    : (color || 'bg-blue-600 text-white hover:bg-blue-700')
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
        disabled || loading ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed' : baseColor
      }`}
    >
      {loading ? '处理中...' : label}
    </button>
  )
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
      <h2 className="text-sm font-medium text-white mb-2">{title}</h2>
      {children}
    </div>
  )
}

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

function ConfirmModal({ open, title, message, onConfirm, onCancel, loading, variant }: {
  open: boolean; title: string; message: string; onConfirm: () => void; onCancel: () => void; loading?: boolean; variant?: 'danger' | 'warning' | 'default'
}) {
  if (!open) return null
  const btnColor = variant === 'danger'
    ? 'bg-red-600 hover:bg-red-700'
    : variant === 'warning'
    ? 'bg-yellow-600 hover:bg-yellow-700'
    : 'bg-blue-600 hover:bg-blue-700'
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-zinc-900 border border-[var(--card-border)] rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
        <h3 className="text-white font-medium mb-2">{title}</h3>
        <p className="text-sm text-[var(--muted)] mb-6 whitespace-pre-wrap">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 rounded text-sm text-[var(--muted)] hover:text-white bg-zinc-800 hover:bg-zinc-700 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`px-4 py-2 rounded text-sm text-white transition-colors ${btnColor} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? '处理中...' : '确认'}
          </button>
        </div>
      </div>
    </div>
  )
}

function DiffViewer({ diff }: { diff: string }) {
  const lines = diff.split('\n')
  return (
    <pre className="text-xs font-mono leading-5 bg-black/30 rounded-lg p-3 overflow-x-auto max-h-96 overflow-y-auto">
      {lines.map((line, i) => {
        let color = ''
        if (line.startsWith('+')) color = 'text-green-400'
        else if (line.startsWith('-')) color = 'text-red-400'
        else if (line.startsWith('@@')) color = 'text-cyan-400'
        else if (line.startsWith('diff --git') || line.startsWith('index ') || line.startsWith('---') || line.startsWith('+++')) color = 'text-zinc-500'
        return (
          <div key={i} className={`${color} whitespace-pre`}>{line}</div>
        )
      })}
    </pre>
  )
}

function CheckResultCard({ check }: { check: CheckItem }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className={`border rounded-lg p-3 text-sm ${check.passed ? 'border-green-500/30 bg-green-500/5' : check.blocking ? 'border-red-500/30 bg-red-500/5' : 'border-yellow-500/30 bg-yellow-500/5'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>{check.passed ? '✅' : check.blocking ? '❌' : '⚠️'}</span>
          <span className="text-white">{check.name}</span>
          {check.blocking && !check.passed && (
            <span className="text-[10px] bg-red-500/10 text-red-400 px-1.5 rounded border border-red-500/30">阻塞</span>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-[var(--muted)] hover:text-white"
        >
          {expanded ? '收起' : '展开日志'}
        </button>
      </div>
      {expanded && check.output && (
        <pre className="text-xs text-white/60 mt-2 p-2 bg-black/30 rounded max-h-40 overflow-y-auto font-mono whitespace-pre-wrap">
          {check.output}
        </pre>
      )}
    </div>
  )
}

// ── Page ──

export default function CodeChangeDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)
  const [request, setRequest] = useState<CCR | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Confirmation modal state
  const [confirmAction, setConfirmAction] = useState<{ title: string; message: string; action: string; variant?: 'danger' | 'warning' } | null>(null)

  const load = () => {
    if (!id) return
    getCodeChangeRequest(id)
      .then(setRequest)
      .catch(() => setError('无法加载代码变更请求'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const doAction = async (action: string, fn: () => Promise<any>) => {
    setConfirmAction(null)
    setActionLoading(action)
    setActionMsg(null)
    try {
      const r = await fn()
      const msgs: Record<string, string> = {
        'generate-plan': '✅ 方案已生成',
        'approve-plan': '✅ 方案已批准',
        'generate-patch': '✅ 补丁已生成',
        'run-checks': '✅ 检查已完成',
        'apply': '✅ 已应用',
        'rollback': '✅ 已回滚',
        'reject': '✅ 已拒绝',
        'revise': '✅ 已退回修订',
      }
      setActionMsg(msgs[action] || `✅ 操作成功 — ${r.status}`)
      await load()
    } catch (e: any) {
      setActionMsg(`❌ 操作失败: ${e.message || '未知错误'}`)
    } finally {
      setActionLoading(null)
    }
  }

  const askConfirm = (action: string) => {
    const confirmations: Record<string, { title: string; message: string; variant?: 'danger' | 'warning' }> = {
      'approve-plan': { title: '批准方案', message: '确认批准此方案？批准后将生成代码补丁。' },
      'generate-patch': { title: '生成补丁', message: '将调用 Coding Agent 生成代码变更补丁。' },
      'apply': { title: '应用代码变更', message: '将把补丁写入工作目录。\n\n建议先确认 Checks 结果。\n\n确认应用？', variant: 'warning' },
      'rollback': { title: '回滚代码变更', message: '将撤销之前应用的修改。\n\n此操作有风险，确认回滚？', variant: 'danger' },
      'reject': { title: '拒绝请求', message: '确认拒绝此请求？拒绝后无法恢复。', variant: 'danger' },
      'revise': { title: '退回修订', message: '将此请求退回方案审批阶段进行修改。', variant: 'warning' },
    }
    setConfirmAction({
      ...(confirmations[action] || { title: '确认操作', message: '确认执行此操作？' }),
      action,
    })
  }

  const confirmAndDo = (action: string, fn: () => Promise<any>) => {
    doAction(action, fn)
  }

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

  // ── State machine steps ──
  const status = request.status
  const steps = [
    { label: '方案', done: ['plan_generated', 'plan_approved', 'patch_generated', 'checks_passed', 'checks_warning', 'checks_failed', 'applied', 'rolled_back', 'rejected'].includes(status), active: status === 'draft' || status === 'plan_generated' },
    { label: '审批', done: ['plan_approved', 'patch_generated', 'checks_passed', 'checks_warning', 'checks_failed', 'applied', 'rolled_back'].includes(status), active: status === 'plan_approved' },
    { label: '补丁', done: ['patch_generated', 'checks_passed', 'checks_warning', 'checks_failed', 'applied', 'rolled_back'].includes(status), active: status === 'patch_generated' },
    { label: '检查', done: ['checks_passed', 'checks_warning', 'checks_failed'].includes(status), active: ['checks_passed', 'checks_warning', 'checks_failed'].includes(status) },
    { label: '应用', done: ['applied', 'rolled_back'].includes(status), active: status === 'applied' },
  ]
  if (status === 'rejected') {
    steps.push({ label: '已拒绝', done: false, active: true })
  } else if (status === 'rolled_back') {
    steps.push({ label: '已回滚', done: false, active: true })
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back link */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.push('/code-change-requests')} className="text-sm text-[var(--muted)] hover:text-white">
          ← 回到代码桥
        </button>
      </div>

      {/* Title + Status */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-medium text-white">{request.title}</h1>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <StatusBadge status={request.status} />
            {request.applied_with_warning && (
              <span className="text-[10px] bg-yellow-500/10 text-yellow-400 px-1.5 rounded border border-yellow-500/30">
                ⚠️ 带警告应用
              </span>
            )}
            <span className={`text-xs ${RISK_COLORS[request.risk_level] || ''}`}>
              {request.risk_level.toUpperCase()} RISK
            </span>
            {request.runtime_id && (
              <span className="px-2 py-0.5 rounded text-xs border bg-zinc-800 text-zinc-400 border-zinc-700">
                {request.runtime_id}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Plan section */}
      {(request.problem_summary || request.plan_summary || request.impact_scope) && (
        <SectionCard title="📋 方案">
          <div className="text-xs text-white/70 space-y-3">
            {request.problem_summary && (
              <div>
                <div className="text-[var(--muted)] mb-0.5 text-[10px]">💡 问题描述</div>
                <div className="whitespace-pre-wrap">{request.problem_summary}</div>
              </div>
            )}
            {request.plan_summary && (
              <div>
                <div className="text-[var(--muted)] mb-0.5 text-[10px]">📝 方案摘要</div>
                <div className="whitespace-pre-wrap">{request.plan_summary}</div>
              </div>
            )}
            {request.impact_scope && (
              <div>
                <div className="text-[var(--muted)] mb-0.5 text-[10px]">🎯 影响范围</div>
                <div className="whitespace-pre-wrap">{request.impact_scope}</div>
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* Files section */}
      {(request.files_expected.length > 0 || (request.files_changed?.length || 0) > 0) && (
        <SectionCard title="📁 文件列表">
          <div className="space-y-2">
            {request.files_expected.length > 0 && (
              <div>
                <div className="text-[10px] text-[var(--muted)] mb-1">预计修改</div>
                <div className="flex flex-wrap gap-1">
                  {request.files_expected.map(f => (
                    <span key={f} className="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {request.files_changed?.length > 0 && (
              <div>
                <div className="text-[10px] text-[var(--muted)] mb-1">实际变更</div>
                <div className="flex flex-wrap gap-1">
                  {request.files_changed.map(f => (
                    <span key={f} className="text-[10px] bg-blue-900/30 text-blue-300 px-1.5 py-0.5 rounded font-mono">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* Patch diff */}
      {request.patch_diff && (
        <SectionCard title="🔄 Diff 补丁">
          <DiffViewer diff={request.patch_diff} />
          {request.diff_summary && (
            <div className="mt-2 text-xs text-[var(--muted)]">
              {request.diff_summary}
            </div>
          )}
        </SectionCard>
      )}

      {/* Check results */}
      {request.check_result && (
        <SectionCard title="🔍 自动检查结果">
          <div className="space-y-2">
            {Object.entries(request.check_result).map(([key, check]) => (
              <CheckResultCard key={key} check={check} />
            ))}
          </div>
        </SectionCard>
      )}

      {/* Protected file check */}
      {request.protected_file_check && (
        <SectionCard title="🛡️ 受保护文件检查">
          <div className="space-y-2 text-xs">
            {request.protected_file_check.pre_check && (
              <div className={`p-2 rounded ${request.protected_file_check.pre_check.passed ? 'bg-green-500/5 border border-green-500/30' : 'bg-red-500/5 border border-red-500/30'}`}>
                <div className="font-medium mb-1">{request.protected_file_check.pre_check.passed ? '✅ 预检查通过' : '❌ 预检查失败'}</div>
                {request.protected_file_check.pre_check.files?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {request.protected_file_check.pre_check.files.map(f => (
                      <span key={f} className="text-[10px] bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded font-mono">{f}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
            {request.protected_file_check.post_check && (
              <div className={`p-2 rounded ${request.protected_file_check.post_check.passed ? 'bg-green-500/5 border border-green-500/30' : 'bg-red-500/5 border border-red-500/30'}`}>
                <div className="font-medium mb-1">{request.protected_file_check.post_check.passed ? '✅ 事后检查通过' : '❌ 事后检查失败'}</div>
                {request.protected_file_check.post_check.files?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {request.protected_file_check.post_check.files.map(f => (
                      <span key={f} className="text-[10px] bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded font-mono">{f}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* State machine progress */}
      <SectionCard title="📌 执行流程">
        <div className="flex items-center gap-4 justify-center flex-wrap">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-4">
              <StepIndicator label={s.label} done={s.done} active={s.active} index={i + 1} />
              {i < steps.length - 1 && (
                <div className={`w-6 h-px ${s.done ? 'bg-green-500/50' : 'bg-zinc-700'}`} />
              )}
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Audit trail */}
      <SectionCard title="📜 审计记录">
        <div className="text-xs text-[var(--muted)] space-y-1">
          {request.created_at && <div>创建时间: {new Date(request.created_at).toLocaleString('zh-CN')}</div>}
          {request.plan_approved_by && <div>方案批准: {request.plan_approved_by} · {request.plan_approved_at && new Date(request.plan_approved_at).toLocaleString('zh-CN')}</div>}
          {request.applied_by && <div>应用人: {request.applied_by} · {request.applied_at && new Date(request.applied_at).toLocaleString('zh-CN')}</div>}
          {request.rolled_back_by && <div>回滚人: {request.rolled_back_by} · {request.rolled_back_at && new Date(request.rolled_back_at).toLocaleString('zh-CN')}</div>}
        </div>
      </SectionCard>

      {/* ── Action buttons ── */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-medium text-white">操作</h2>

        {/* draft — generate plan */}
        {status === 'draft' && (
          <div className="flex gap-2">
            <ActionButton
              label="🔮 生成方案"
              onClick={() => askConfirm('generate-plan')}
              loading={actionLoading === 'generate-plan'}
            />
          </div>
        )}

        {/* plan_generated — approve or reject */}
        {status === 'plan_generated' && (
          <div className="flex gap-2 flex-wrap">
            <ActionButton
              label="✅ 批准方案"
              onClick={() => askConfirm('approve-plan')}
              loading={actionLoading === 'approve-plan'}
            />
            <ActionButton
              label="❌ 拒绝"
              variant="danger"
              onClick={() => askConfirm('reject')}
              loading={actionLoading === 'reject'}
            />
          </div>
        )}

        {/* plan_approved — generate patch */}
        {status === 'plan_approved' && (
          <div className="flex gap-2 flex-wrap">
            <ActionButton
              label="🔧 生成补丁"
              onClick={() => askConfirm('generate-patch')}
              loading={actionLoading === 'generate-patch'}
            />
            <ActionButton
              label="❌ 拒绝"
              variant="danger"
              onClick={() => askConfirm('reject')}
              loading={actionLoading === 'reject'}
            />
          </div>
        )}

        {/* patch_generated — run checks */}
        {status === 'patch_generated' && (
          <div className="flex gap-2">
            <ActionButton
              label="🔍 运行检查"
              onClick={() => doAction('run-checks', () => apiRunChecks(id))}
              loading={actionLoading === 'run-checks'}
            />
          </div>
        )}

        {/* checks_passed — apply */}
        {status === 'checks_passed' && (
          <div className="flex gap-2 flex-wrap">
            <ActionButton
              label="✅ 应用变更"
              color="bg-green-600 text-white hover:bg-green-700"
              onClick={() => askConfirm('apply')}
              loading={actionLoading === 'apply'}
            />
            <ActionButton
              label="📝 退回修订"
              variant="warning"
              onClick={() => askConfirm('revise')}
              loading={actionLoading === 'revise'}
            />
            <ActionButton
              label="❌ 拒绝"
              variant="danger"
              onClick={() => askConfirm('reject')}
              loading={actionLoading === 'reject'}
            />
          </div>
        )}

        {/* checks_warning — apply with warning */}
        {status === 'checks_warning' && (
          <div className="flex gap-2 flex-wrap">
            <ActionButton
              label="⚠️ 带警告应用"
              variant="warning"
              onClick={() => askConfirm('apply')}
              loading={actionLoading === 'apply'}
            />
            <ActionButton
              label="📝 退回修订"
              variant="warning"
              onClick={() => askConfirm('revise')}
              loading={actionLoading === 'revise'}
            />
            <ActionButton
              label="❌ 拒绝"
              variant="danger"
              onClick={() => askConfirm('reject')}
              loading={actionLoading === 'reject'}
            />
          </div>
        )}

        {/* checks_failed — revise or reject */}
        {status === 'checks_failed' && (
          <div className="flex gap-2 flex-wrap">
            <ActionButton
              label="📝 退回修订"
              variant="warning"
              onClick={() => askConfirm('revise')}
              loading={actionLoading === 'revise'}
            />
            <ActionButton
              label="❌ 拒绝"
              variant="danger"
              onClick={() => askConfirm('reject')}
              loading={actionLoading === 'reject'}
            />
          </div>
        )}

        {/* applied — rollback */}
        {status === 'applied' && (
          <div className="flex gap-2">
            <ActionButton
              label="⏪ 回滚"
              variant="danger"
              onClick={() => askConfirm('rollback')}
              loading={actionLoading === 'rollback'}
            />
          </div>
        )}

        {/* terminal states */}
        {(status === 'rolled_back' || status === 'rejected') && (
          <div className="text-xs text-[var(--muted)]">
            该代码变更请求已{status === 'rolled_back' ? '回滚' : '拒绝'}
          </div>
        )}
      </div>

      {/* Action message */}
      {actionMsg && (
        <div className={`text-sm text-center py-2 rounded bg-zinc-800/50 ${actionMsg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>
          {actionMsg}
        </div>
      )}

      {/* Confirmation modal */}
      <ConfirmModal
        open={confirmAction !== null}
        title={confirmAction?.title || ''}
        message={confirmAction?.message || ''}
        variant={confirmAction?.variant}
        onConfirm={() => {
          if (!confirmAction) return
          const actionMap: Record<string, () => Promise<any>> = {
            'generate-plan': () => apiGeneratePlan(id),
            'approve-plan': () => apiApprovePlan(id),
            'generate-patch': () => apiGeneratePatch(id),
            'apply': () => apiApplyCodeChange(id),
            'rollback': () => apiRollbackCodeChange(id),
            'reject': () => apiRejectCodeChange(id),
            'revise': () => apiReviseCodeChange(id),
          }
          confirmAndDo(confirmAction.action, actionMap[confirmAction.action])
        }}
        onCancel={() => setConfirmAction(null)}
        loading={actionLoading !== null}
      />
    </div>
  )
}
