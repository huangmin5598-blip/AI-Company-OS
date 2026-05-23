'use client'

import { useEffect, useState } from 'react'
import { getGoalSessions, createGoalSession, getCeoActionLogs } from '@/lib/api'
import type { GoalSession, CeoActionLog } from '@/types/api'

export default function CeoWorkbenchPage() {
  const [goalSessions, setGoalSessions] = useState<GoalSession[]>([])
  const [actionLogs, setActionLogs] = useState<CeoActionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [rawGoal, setRawGoal] = useState('')
  const [businessLine, setBusinessLine] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [expandedGoalId, setExpandedGoalId] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [goals, logs] = await Promise.all([
        getGoalSessions(),
        getCeoActionLogs(),
      ])
      setGoalSessions(goals.slice(0, 10))
      setActionLogs(logs.slice(0, 10))
    } catch (e) {
      console.error('Failed to load CEO data', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateGoal() {
    if (!rawGoal.trim()) return
    setSubmitting(true)
    try {
      await createGoalSession({
        raw_goal: rawGoal.trim(),
        business_line: businessLine.trim() || undefined,
      })
      setRawGoal('')
      setBusinessLine('')
      await loadData()
    } catch (e) {
      console.error('Failed to create goal session', e)
    } finally {
      setSubmitting(false)
    }
  }

  function statusBadgeColor(status: string): string {
    switch (status) {
      case 'draft': return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
      case 'decomposed': return 'bg-blue-500/20 text-blue-300 border-blue-500/40'
      case 'committed': return 'bg-green-500/20 text-green-300 border-green-500/40'
      case 'cancelled': return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
      case 'failed': return 'bg-red-500/20 text-red-300 border-red-500/40'
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
    }
  }

  function logResultColor(status: string): string {
    switch (status) {
      case 'success': return 'bg-green-500/20 text-green-300 border-green-500/40'
      case 'failed': return 'bg-red-500/20 text-red-300 border-red-500/40'
      case 'ambiguous': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      case 'cancelled': return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  function intentIcon(intent: string): string {
    switch (intent) {
      case 'goal_intake': return '🎯'
      case 'approval_action': return '✅'
      default: return '📋'
    }
  }

  if (loading) {
    return <div className="text-[var(--muted)] text-center py-16">加载中...</div>
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🤖 CEO Workbench</h1>
        <p className="text-sm text-[var(--muted)] mt-1">
          Actual conversation happens via Feishu / Hermes TUI. The CC Panel shows results.
        </p>
      </div>

      {/* Create Goal Section */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-6">
        <h2 className="text-sm font-semibold text-white mb-4">创建目标</h2>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={rawGoal}
            onChange={(e) => setRawGoal(e.target.value)}
            placeholder="输入目标描述..."
            className="flex-1 bg-[var(--background)] border border-[var(--card-border)] rounded-lg px-4 py-2.5 text-sm text-white placeholder-[var(--muted)] focus:outline-none focus:border-[var(--accent)]"
            onKeyDown={(e) => e.key === 'Enter' && handleCreateGoal()}
          />
          <input
            type="text"
            value={businessLine}
            onChange={(e) => setBusinessLine(e.target.value)}
            placeholder="业务线（可选）"
            className="w-40 bg-[var(--background)] border border-[var(--card-border)] rounded-lg px-4 py-2.5 text-sm text-white placeholder-[var(--muted)] focus:outline-none focus:border-[var(--accent)]"
          />
          <button
            onClick={handleCreateGoal}
            disabled={submitting || !rawGoal.trim()}
            className="px-6 py-2.5 bg-[var(--accent)] text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? '提交中...' : '提交'}
          </button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Goal Sessions */}
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">最新目标</h2>
          {goalSessions.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">暂无目标记录</p>
          ) : (
            <div className="space-y-2">
              {goalSessions.map((goal) => (
                <div key={goal.id}>
                  <button
                    onClick={() => setExpandedGoalId(expandedGoalId === goal.id ? null : goal.id)}
                    className="w-full flex items-center justify-between gap-3 p-3 rounded-lg bg-[var(--background)] border border-[var(--card-border)] hover:border-[var(--accent)] transition-colors text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white truncate">
                          {goal.raw_goal.length > 60 ? goal.raw_goal.slice(0, 60) + '…' : goal.raw_goal}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusBadgeColor(goal.status)}`}>
                          {goal.status}
                        </span>
                        {goal.goal_type && (
                          <span className="text-[10px] text-[var(--muted)]">{goal.goal_type}</span>
                        )}
                        {goal.business_line && (
                          <span className="text-[10px] text-[var(--muted)]">{goal.business_line}</span>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] text-[var(--muted)] whitespace-nowrap">
                      {formatDate(goal.created_at)}
                    </span>
                  </button>
                  {expandedGoalId === goal.id && (
                    <div className="mt-1 mx-3 p-3 rounded-lg bg-zinc-800/40 border border-[var(--card-border)] text-xs text-[var(--muted)] space-y-1">
                      {goal.interpreted_goal && (
                        <p><span className="text-white">解析目标:</span> {goal.interpreted_goal}</p>
                      )}
                      {goal.confidence !== null && (
                        <p><span className="text-white">置信度:</span> {(goal.confidence * 100).toFixed(0)}%</p>
                      )}
                      {goal.task_ids_json && (
                        <p><span className="text-white">任务IDs:</span> {goal.task_ids_json}</p>
                      )}
                      {goal.approval_ids_json && (
                        <p><span className="text-white">审批IDs:</span> {goal.approval_ids_json}</p>
                      )}
                      {goal.error_message && (
                        <p className="text-red-400"><span className="text-white">错误:</span> {goal.error_message}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Logs */}
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">最新操作日志</h2>
          {actionLogs.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">暂无操作日志</p>
          ) : (
            <div className="space-y-2">
              {actionLogs.map((log) => (
                <div key={log.id} className="p-3 rounded-lg bg-[var(--background)] border border-[var(--card-border)]">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{intentIcon(log.intent_type)}</span>
                      <span className="text-[10px] text-[var(--muted)]">{log.intent_type}</span>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${logResultColor(log.result_status)}`}>
                      {log.result_status}
                    </span>
                  </div>
                  <p className="text-xs text-white mt-1 line-clamp-2">{log.raw_user_message}</p>
                  <div className="flex items-center gap-3 mt-1">
                    {log.target_type && log.target_id !== null && (
                      <span className="text-[10px] text-[var(--muted)]">
                        {log.target_type} #{log.target_id}
                      </span>
                    )}
                    {log.confidence !== null && (
                      <span className="text-[10px] text-[var(--muted)]">
                        置信度: {(log.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                    <span className="text-[10px] text-[var(--muted)]">{formatDate(log.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-6">
        <h2 className="text-sm font-semibold text-white mb-4">快捷入口</h2>
        <div className="flex flex-wrap gap-3">
          <a
            href="/approvals"
            className="px-4 py-2 bg-[var(--background)] border border-[var(--card-border)] rounded-lg text-sm text-[var(--muted)] hover:text-white hover:border-[var(--accent)] transition-colors"
          >
            📋 前往 Approval Center
          </a>
          <a
            href="/task-pool"
            className="px-4 py-2 bg-[var(--background)] border border-[var(--card-border)] rounded-lg text-sm text-[var(--muted)] hover:text-white hover:border-[var(--accent)] transition-colors"
          >
            📌 前往 TASK-POOL
          </a>
        </div>
      </div>
    </div>
  )
}
