'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getTaskPoolItem, getContextPack, getApprovals, createApproval, updateTaskPoolItem, createReview, getLearningCandidates } from '@/lib/api'
import type { TaskPoolItem, ContextPack, ApprovalItem, ReviewItem, LearningCandidate } from '@/types/api'

const STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  draft:              { label: '草稿',              color: 'text-gray-400',    bg: 'bg-gray-500/10' },
  ready:              { label: '就绪',              color: 'text-blue-400',    bg: 'bg-blue-500/10' },
  approval_required:  { label: '待审批',            color: 'text-yellow-400',  bg: 'bg-yellow-500/10' },
  approved:           { label: '已批准',            color: 'text-green-400',   bg: 'bg-green-500/10' },
  running:            { label: '执行中',            color: 'text-cyan-400',    bg: 'bg-cyan-500/10' },
  review:             { label: '待验收',            color: 'text-purple-400',  bg: 'bg-purple-500/10' },
  done:               { label: '完成',              color: 'text-green-400',   bg: 'bg-green-500/10' },
  blocked:            { label: '阻塞',              color: 'text-red-400',     bg: 'bg-red-500/10' },
  cancelled:          { label: '取消',              color: 'text-gray-500',    bg: 'bg-gray-500/10' },
  revision_required:  { label: '需修改',            color: 'text-orange-400',  bg: 'bg-orange-500/10' },
}

const SOURCE_ICON: Record<string, string> = {
  alert: '🔔', command: '⚡', manual: '✏️', cron: '⏰',
}

const PRIORITY_LABEL: Record<string, string> = {
  critical: '🔴 紧急', high: '🟠 高', medium: '🟡 中', low: '🟢 低',
}

const RISK_LABEL: Record<string, string> = {
  high: '🔴 高', medium: '🟡 中', low: '🟢 低',
}

export default function TaskDetailPage() {
  const params = useParams()
  const router = useRouter()
  const taskId = Number(params.id)

  const [task, setTask] = useState<TaskPoolItem | null>(null)
  const [contextPack, setContextPack] = useState<ContextPack | null>(null)
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'context' | 'approvals' | 'reviews' | 'learning' | 'related'>('context')

  // For context pack edit
  const [editingPack, setEditingPack] = useState(false)
  const [editPackData, setEditPackData] = useState<Partial<ContextPack>>({})

  // For review form
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [reviewResult, setReviewResult] = useState('pass')
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewNextAction, setReviewNextAction] = useState('')
  const [submittingReview, setSubmittingReview] = useState(false)

  // For approval
  const [showApprovalForm, setShowApprovalForm] = useState(false)
  const [approvalReason, setApprovalReason] = useState('')
  const [submittingApproval, setSubmittingApproval] = useState(false)

  // For execute action
  const [executing, setExecuting] = useState(false)

  // Review records (from approvals or inline created)
  const [reviews, setReviews] = useState<ReviewItem[]>([])

  // Learning candidates for this task
  const [learningCandidates, setLearningCandidates] = useState<LearningCandidate[]>([])

  useEffect(() => {
    async function load() {
      try {
        const [t, ap] = await Promise.all([
          getTaskPoolItem(taskId),
          getApprovals({ target_type: 'task' }).catch(() => [] as ApprovalItem[]),
        ])
        setTask(t)
        // Filter approvals for this task
        const taskApprovals = (ap as ApprovalItem[]).filter(a => a.target_id === taskId)
        setApprovals(taskApprovals)

        // Try to load context pack
        try {
          const cp = await getContextPack(taskId)
          setContextPack(cp)
          setEditPackData({
            founder_intent: cp.founder_intent,
            business_line_state: cp.business_line_state,
            related_runs: cp.related_runs,
            related_artifacts: cp.related_artifacts,
            known_failures: cp.known_failures,
            relevant_rules: cp.relevant_rules,
            constraints: cp.constraints,
            forbidden_actions: cp.forbidden_actions,
            budget_limit: cp.budget_limit,
            acceptance_criteria: cp.acceptance_criteria,
            referenced_knowledge: cp.referenced_knowledge,
          })
        } catch {
          // context pack may not exist yet
        }

        setError(null)

        // Load learning candidates for this task
        try {
          const allLcs = await getLearningCandidates()
          const taskLcs = allLcs.filter(lc =>
            lc.source_type === 'failure' && lc.source_id === `task:${taskId}` ||
            lc.source_id === String(taskId)
          )
          setLearningCandidates(taskLcs)
        } catch {
          // optional
        }
      } catch (e) {
        setError('加载任务详情失败')
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [taskId])

  async function handleSubmitApproval() {
    if (!task) return
    setSubmittingApproval(true)
    try {
      await createApproval({
        target_type: 'task',
        target_id: task.id,
        risk_level: task.risk_level || 'medium',
        reason: approvalReason || undefined,
      })
      setShowApprovalForm(false)
      setApprovalReason('')
      // Reload task
      const t = await getTaskPoolItem(taskId)
      setTask(t)
    } catch (e) {
      console.error('Failed to submit approval', e)
    } finally {
      setSubmittingApproval(false)
    }
  }

  async function handleExecute() {
    if (!task) return
    setExecuting(true)
    try {
      await updateTaskPoolItem(taskId, { status: 'running' } as Record<string, unknown>)
      const t = await getTaskPoolItem(taskId)
      setTask(t)
    } catch (e) {
      console.error('Failed to execute task', e)
    } finally {
      setExecuting(false)
    }
  }

  async function handleSubmitReview() {
    if (!task) return
    setSubmittingReview(true)
    try {
      await createReview({
        task_id: task.id,
        result: reviewResult,
        review_notes: reviewNotes || undefined,
        next_action: reviewNextAction || undefined,
      })
      // Update task status based on result
      let newStatus = 'done'
      if (reviewResult === 'revision_required') newStatus = 'revision_required'
      if (reviewResult === 'blocked') newStatus = 'blocked'
      await updateTaskPoolItem(taskId, { status: newStatus } as Record<string, unknown>)

      setShowReviewForm(false)
      setReviewResult('pass')
      setReviewNotes('')
      setReviewNextAction('')
      const t = await getTaskPoolItem(taskId)
      setTask(t)
    } catch (e) {
      console.error('Failed to submit review', e)
    } finally {
      setSubmittingReview(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
  }

  if (error || !task) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <div className="text-red-400">⚠️ {error || '任务未找到'}</div>
        <button onClick={() => router.push('/task-pool')} className="text-sm text-blue-400 hover:text-blue-300">
          ← 返回任务列表
        </button>
      </div>
    )
  }

  const cfg = STATUS_MAP[task.status] || STATUS_MAP.draft
  const srcIcon = SOURCE_ICON[task.source] || '📋'

  return (
    <div className="space-y-4">
      {/* Back button */}
      <button onClick={() => router.push('/task-pool')} className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
        ← 返回任务列表
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* ── Left Panel: Task Info ── */}
        <div className="lg:col-span-3 space-y-4">
          {/* Status + Title */}
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.color} ${cfg.bg}`}>
                {cfg.label}
              </span>
              <span className="text-[10px] text-[var(--muted)]">#{task.id}</span>
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">{task.title}</h2>
            {task.description && (
              <p className="text-sm text-zinc-300 mb-3">{task.description}</p>
            )}
          </div>

          {/* Metadata Grid */}
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
            <h3 className="text-sm font-medium text-[var(--muted)] mb-3">任务信息</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <MetaItem label="来源" value={<span>{srcIcon} {task.source}</span>} />
              <MetaItem label="业务线" value={task.business_line || '-'} />
              <MetaItem label="优先级" value={PRIORITY_LABEL[task.priority] || task.priority} />
              <MetaItem label="风险等级" value={RISK_LABEL[task.risk_level] || task.risk_level} />
              <MetaItem label="负责 Agent" value={task.assigned_agent || '-'} />
              <MetaItem label="成本" value={`$${task.cost_usd.toFixed(6)}`} />
              {task.created_at && (
                <MetaItem label="创建时间" value={new Date(task.created_at).toLocaleString('zh-CN')} />
              )}
              {task.completed_at && (
                <MetaItem label="完成时间" value={new Date(task.completed_at).toLocaleString('zh-CN')} />
              )}
            </div>
          </div>

          {/* Acceptance Criteria */}
          {task.acceptance_criteria && (
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
              <h3 className="text-sm font-medium text-[var(--muted)] mb-2">📐 验收标准</h3>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap">{task.acceptance_criteria}</p>
            </div>
          )}

          {/* Result / Error */}
          {task.result_summary && (
            <div className="bg-[var(--card)] border border-green-500/20 rounded-lg p-4">
              <h3 className="text-sm font-medium text-green-400 mb-2">✅ 执行结果</h3>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap">{task.result_summary}</p>
            </div>
          )}
          {task.error_message && (
            <div className="bg-[var(--card)] border border-red-500/20 rounded-lg p-4">
              <h3 className="text-sm font-medium text-red-400 mb-2">❌ 错误信息</h3>
              <p className="text-sm text-red-300 whitespace-pre-wrap">{task.error_message}</p>
              {task.failure_reason && (
                <p className="text-xs text-red-400/70 mt-1">原因: {task.failure_reason}</p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {task.status === 'approval_required' && (
              !showApprovalForm ? (
                <button
                  onClick={() => setShowApprovalForm(true)}
                  className="px-4 py-2 bg-yellow-600/20 border border-yellow-600/40 text-yellow-400 rounded text-sm hover:bg-yellow-600/30 transition-colors"
                >
                  📨 提交审批
                </button>
              ) : (
                <div className="w-full bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
                  <h4 className="text-sm font-medium text-white">提交审批请求</h4>
                  <textarea
                    placeholder="审批理由（可选）"
                    value={approvalReason}
                    onChange={e => setApprovalReason(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white resize-none h-20"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSubmitApproval}
                      disabled={submittingApproval}
                      className="px-4 py-1.5 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700 transition-colors disabled:opacity-50"
                    >
                      {submittingApproval ? '提交中...' : '确认提交'}
                    </button>
                    <button
                      onClick={() => setShowApprovalForm(false)}
                      className="px-4 py-1.5 bg-zinc-800 text-zinc-300 rounded text-sm hover:bg-zinc-700 transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              )
            )}

            {task.status === 'approved' && (
              <button
                onClick={handleExecute}
                disabled={executing}
                className="px-4 py-2 bg-green-600/20 border border-green-600/40 text-green-400 rounded text-sm hover:bg-green-600/30 transition-colors disabled:opacity-50"
              >
                {executing ? '执行中...' : '▶️ 执行'}
              </button>
            )}

            {task.status === 'review' && (
              !showReviewForm ? (
                <button
                  onClick={() => setShowReviewForm(true)}
                  className="px-4 py-2 bg-purple-600/20 border border-purple-600/40 text-purple-400 rounded text-sm hover:bg-purple-600/30 transition-colors"
                >
                  📝 提交验收
                </button>
              ) : (
                <div className="w-full bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 space-y-3">
                  <h4 className="text-sm font-medium text-white">提交验收结果</h4>
                  <select
                    value={reviewResult}
                    onChange={e => setReviewResult(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
                  >
                    <option value="pass">✅ 通过</option>
                    <option value="revision_required">🔄 需修改</option>
                    <option value="blocked">🚫 阻塞</option>
                  </select>
                  <textarea
                    placeholder="验收备注"
                    value={reviewNotes}
                    onChange={e => setReviewNotes(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white resize-none h-20"
                  />
                  <input
                    type="text"
                    placeholder="下一步操作（可选）"
                    value={reviewNextAction}
                    onChange={e => setReviewNextAction(e.target.value)}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSubmitReview}
                      disabled={submittingReview}
                      className="px-4 py-1.5 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      {submittingReview ? '提交中...' : '确认提交'}
                    </button>
                    <button
                      onClick={() => setShowReviewForm(false)}
                      className="px-4 py-1.5 bg-zinc-800 text-zinc-300 rounded text-sm hover:bg-zinc-700 transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              )
            )}

            {task.status === 'running' && (
              <div className="text-sm text-cyan-400 flex items-center gap-2">
                <span className="animate-pulse">🔄</span> 系统正在执行中...
              </div>
            )}

            {(task.status === 'blocked' || task.status === 'revision_required') && (
              <div className="text-sm text-orange-400">
                {task.status === 'revision_required' ? '🔄 需要修改后重新提交' : '🚫 任务被阻塞'}
              </div>
            )}
          </div>
        </div>

        {/* ── Right Panel: Tabs ── */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg overflow-hidden">
            {/* Tab bar */}
            <div className="flex border-b border-[var(--card-border)] overflow-x-auto">
              {(['context', 'approvals', 'reviews', 'learning', 'related'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-2 text-xs whitespace-nowrap transition-colors ${
                    activeTab === tab
                      ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/5'
                      : 'text-[var(--muted)] hover:text-white'
                  }`}
                >
                  {tab === 'context' && '📦 Context Pack'}
                  {tab === 'approvals' && '📋 审批记录'}
                  {tab === 'reviews' && '🔍 Review 记录'}
                  {tab === 'learning' && '🧠 Learning'}
                  {tab === 'related' && '🔗 关联数据'}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="p-4 max-h-[500px] overflow-y-auto">
              {/* Context Pack */}
              {activeTab === 'context' && (
                <div className="space-y-3">
                  {contextPack ? (
                    editingPack ? (
                      <div className="space-y-3">
                        {Object.entries(editPackData).filter(([_, v]) => typeof v !== 'boolean').map(([key, val]) => (
                          <div key={key}>
                            <label className="text-[11px] text-[var(--muted)] block mb-0.5">{key}</label>
                            {typeof val === 'number' ? (
                              <input
                                type="number"
                                value={val}
                                onChange={e => setEditPackData(p => ({ ...p, [key]: e.target.value ? Number(e.target.value) : null }))}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-white"
                              />
                            ) : (
                              <textarea
                                value={String(val ?? '')}
                                onChange={e => setEditPackData(p => ({ ...p, [key]: e.target.value }))}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-white resize-none h-16"
                              />
                            )}
                          </div>
                        ))}
                        <div className="flex gap-2 pt-2">
                          <button
                            onClick={async () => {
                              try {
                                const { upsertContextPack } = await import('@/lib/api')
                                const updated = await upsertContextPack(taskId, editPackData)
                                setContextPack(updated)
                                setEditingPack(false)
                              } catch (e) { console.error(e) }
                            }}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
                          >
                            保存
                          </button>
                          <button
                            onClick={() => { setEditingPack(false); setEditPackData({ ...contextPack }) }}
                            className="px-3 py-1 bg-zinc-800 text-zinc-300 rounded text-xs hover:bg-zinc-700 transition-colors"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-[var(--muted)]">Context Pack #{contextPack.id}</span>
                          {contextPack.auto_generated && (
                            <span className="text-[10px] bg-yellow-500/10 text-yellow-400 px-1.5 py-0.5 rounded border border-yellow-500/30">
                              (草稿)
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => setEditingPack(true)}
                          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          ✏️ 编辑
                        </button>
                        <ContextPackField label="Founder Intent" value={contextPack.founder_intent} />
                        <ContextPackField label="Business Line State" value={contextPack.business_line_state} />
                        <ContextPackField label="Constraints" value={contextPack.constraints} />
                        <ContextPackField label="Forbidden Actions" value={contextPack.forbidden_actions} />
                        <ContextPackField label="Budget Limit" value={contextPack.budget_limit != null ? `$${contextPack.budget_limit}` : null} />
                        <ContextPackField label="Acceptance Criteria" value={contextPack.acceptance_criteria} />
                        <ContextPackField label="Related Runs" value={formatJsonList(contextPack.related_runs)} />
                        <ContextPackField label="Related Artifacts" value={formatJsonList(contextPack.related_artifacts)} />
                        <ContextPackField label="Known Failures" value={formatList(contextPack.known_failures)} />
                        <ContextPackField label="Referenced Knowledge" value={contextPack.referenced_knowledge} />
                      </div>
                    )
                  ) : (
                    <div className="text-xs text-[var(--muted)] text-center py-8">
                      Context Pack 未生成。系统将在任务执行时自动生成。
                    </div>
                  )}
                </div>
              )}

              {/* Approval Records */}
              {activeTab === 'approvals' && (
                <div className="space-y-3">
                  {approvals.length === 0 ? (
                    <div className="text-xs text-[var(--muted)] text-center py-8">暂无审批记录</div>
                  ) : (
                    approvals.map(a => (
                      <div key={a.id} className="bg-zinc-800/50 rounded p-3 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-white">#{a.id}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                            a.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                            a.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                            a.status === 'deferred' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {a.status}
                          </span>
                        </div>
                        {a.reason && <div className="text-xs text-zinc-300">理由: {a.reason}</div>}
                        {a.founder_decision && <div className="text-xs text-zinc-300">决定: {a.founder_decision}</div>}
                        {a.founder_notes && <div className="text-xs text-zinc-400">备注: {a.founder_notes}</div>}
                        {a.created_at && (
                          <div className="text-[10px] text-[var(--muted)]">
                            {new Date(a.created_at).toLocaleString('zh-CN')}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Review Records */}
              {activeTab === 'reviews' && (
                <div className="space-y-3">
                  {reviews.length === 0 ? (
                    <div className="text-xs text-[var(--muted)] text-center py-8">暂无验收记录</div>
                  ) : (
                    reviews.map(r => (
                      <div key={r.id} className="bg-zinc-800/50 rounded p-3 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                            r.result === 'pass' ? 'bg-green-500/20 text-green-400' :
                            r.result === 'revision_required' ? 'bg-orange-500/20 text-orange-400' :
                            'bg-red-500/20 text-red-400'
                          }`}>
                            {r.result === 'pass' ? '✅ 通过' : r.result === 'revision_required' ? '🔄 需修改' : '🚫 阻塞'}
                          </span>
                          <span className="text-[10px] text-[var(--muted)]">by {r.reviewed_by}</span>
                        </div>
                        {r.review_notes && <div className="text-xs text-zinc-300">{r.review_notes}</div>}
                        {r.next_action && <div className="text-xs text-blue-400">下一步: {r.next_action}</div>}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Learning Candidates */}
              {activeTab === 'learning' && (
                <div className="space-y-3">
                  {learningCandidates.length === 0 ? (
                    <div className="text-xs text-[var(--muted)] text-center py-8">
                      暂无 Learning Candidate
                    </div>
                  ) : (
                    learningCandidates.map(lc => (
                      <div key={lc.id} className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-zinc-200">
                            {lc.source_type === 'failure' ? '🔴' : lc.source_type === 'tool_gap' ? '🔧' : '💡'} {lc.candidate_type}
                          </span>
                          <span className={`text-[10px] px-2 py-0.5 rounded ${
                            lc.approval_status === 'approved' ? 'bg-green-500/20 text-green-400' :
                            lc.approval_status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                            lc.approval_status === 'pending_approval' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-zinc-700 text-zinc-400'
                          }`}>
                            #{lc.id} {lc.approval_status}
                          </span>
                        </div>
                        {lc.summary && (
                          <div className="text-xs text-zinc-300">{lc.summary}</div>
                        )}
                        {lc.recommendation && (
                          <div className="text-xs text-blue-300 bg-blue-500/5 border border-blue-500/20 rounded px-2 py-1.5">
                            💡 建议: {lc.recommendation}
                          </div>
                        )}
                        {lc.created_at && (
                          <div className="text-[10px] text-[var(--muted)]">
                            {new Date(lc.created_at).toLocaleString('zh-CN')}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Related Data */}
              {activeTab === 'related' && (
                <div className="space-y-3">
                  {task.source_id ? (
                    <div className="text-xs text-zinc-300">
                      <div>来源类型: {task.source}</div>
                      <div>来源 ID: {task.source_id}</div>
                    </div>
                  ) : (
                    <div className="text-xs text-[var(--muted)] text-center py-8">暂无关联数据</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetaItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="text-white/90">{value}</span>
    </div>
  )
}

function ContextPackField({ label, value }: { label: string; value: string | React.ReactNode | null }) {
  if (!value) return null
  return (
    <div>
      <div className="text-[11px] text-[var(--muted)] mb-0.5">{label}</div>
      <div className="text-xs text-zinc-300 whitespace-pre-wrap">{value}</div>
    </div>
  )
}

function formatJsonList(val: string | null): string | null {
  if (!val) return null
  try {
    const parsed = JSON.parse(val)
    if (Array.isArray(parsed)) return parsed.map((s: string) => `• ${s}`).join('\n')
    return val
  } catch {
    return val
  }
}

function formatList(val: string | null): string | null {
  if (!val) return null
  // If it's already a list-like format
  const lines = val.split(',').map(s => `• ${s.trim()}`)
  if (lines.length > 1) return lines.join('\n')
  return val
}
