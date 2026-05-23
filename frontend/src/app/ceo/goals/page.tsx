'use client'

import { useEffect, useState } from 'react'
import { getGoalSessions } from '@/lib/api'
import type { GoalSession } from '@/types/api'

const STATUS_OPTIONS = ['all', 'draft', 'decomposed', 'committed', 'cancelled', 'failed'] as const
type StatusFilter = (typeof STATUS_OPTIONS)[number]

export default function GoalSessionsPage() {
  const [goals, setGoals] = useState<GoalSession[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  useEffect(() => {
    loadGoals()
  }, [statusFilter])

  async function loadGoals() {
    setLoading(true)
    try {
      const data = await getGoalSessions(
        statusFilter !== 'all' ? { status: statusFilter } : undefined
      )
      setGoals(data.sort((a, b) => {
        const aDate = a.created_at ? new Date(a.created_at).getTime() : 0
        const bDate = b.created_at ? new Date(b.created_at).getTime() : 0
        return bDate - aDate
      }))
    } catch (e) {
      console.error('Failed to load goal sessions', e)
    } finally {
      setLoading(false)
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

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  function parseTasks(taskIdsJson: string | null): string {
    if (!taskIdsJson) return '—'
    try {
      const ids = JSON.parse(taskIdsJson)
      if (Array.isArray(ids)) return ids.join(', ')
      return taskIdsJson
    } catch {
      return taskIdsJson
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🎯 Goal Sessions 目标记录</h1>
        <p className="text-sm text-[var(--muted)] mt-1">查看和管理所有目标会话</p>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--muted)]">状态筛选:</span>
        <div className="flex flex-wrap gap-1">
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
                statusFilter === s
                  ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                  : 'bg-[var(--background)] text-[var(--muted)] border-[var(--card-border)] hover:text-white'
              }`}
            >
              {s === 'all' ? '全部' : s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-[var(--muted)] text-center py-16">加载中...</div>
      ) : goals.length === 0 ? (
        <div className="text-[var(--muted)] text-center py-16 bg-[var(--card)] border border-[var(--card-border)] rounded-xl">
          暂无目标记录
        </div>
      ) : (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--card-border)] bg-zinc-800/30">
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">ID</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">目标</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">类型</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">业务线</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">状态</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">任务</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">置信度</th>
                  <th className="text-left text-[var(--muted)] font-medium px-4 py-3 text-xs">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {goals.map((goal) => (
                  <tr key={goal.id} className="border-t border-[var(--card-border)]">
                    <td colSpan={8} className="p-0">
                      <button
                        onClick={() => setExpandedId(expandedId === goal.id ? null : goal.id)}
                        className="w-full flex items-center px-4 py-3 hover:bg-zinc-800/20 transition-colors text-left"
                      >
                        <span className="w-[40px] text-xs text-[var(--muted)]">{goal.id}</span>
                        <span className="flex-1 text-xs text-white truncate pr-2">
                          {goal.raw_goal.length > 50 ? goal.raw_goal.slice(0, 50) + '…' : goal.raw_goal}
                        </span>
                        <span className="w-[80px] text-xs text-[var(--muted)]">{goal.goal_type || '—'}</span>
                        <span className="w-[100px] text-xs text-[var(--muted)]">{goal.business_line || '—'}</span>
                        <span className="w-[100px]">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusBadgeColor(goal.status)}`}>
                            {goal.status}
                          </span>
                        </span>
                        <span className="w-[80px] text-xs text-[var(--muted)]">{parseTasks(goal.task_ids_json)}</span>
                        <span className="w-[60px] text-xs text-[var(--muted)]">
                          {goal.confidence !== null ? `${(goal.confidence * 100).toFixed(0)}%` : '—'}
                        </span>
                        <span className="w-[140px] text-[10px] text-[var(--muted)]">{formatDate(goal.created_at)}</span>
                      </button>
                      {expandedId === goal.id && (
                        <div className="px-4 pb-3 pt-1 mx-4 mb-2 rounded-lg bg-zinc-800/30 border border-[var(--card-border)] text-xs text-[var(--muted)] space-y-1.5">
                          {goal.interpreted_goal && (
                            <p><span className="text-white font-medium">解析目标:</span> {goal.interpreted_goal}</p>
                          )}
                          {goal.decomposition_json && (
                            <p><span className="text-white font-medium">分解结果:</span> {goal.decomposition_json}</p>
                          )}
                          {goal.task_ids_json && (
                            <p><span className="text-white font-medium">任务IDs:</span> {goal.task_ids_json}</p>
                          )}
                          {goal.approval_ids_json && (
                            <p><span className="text-white font-medium">审批IDs:</span> {goal.approval_ids_json}</p>
                          )}
                          {goal.error_message && (
                            <p className="text-red-400"><span className="text-white font-medium">错误信息:</span> {goal.error_message}</p>
                          )}
                          {goal.source_channel && (
                            <p><span className="text-white font-medium">来源渠道:</span> {goal.source_channel}</p>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
