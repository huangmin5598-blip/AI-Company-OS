'use client'

import { useEffect, useState, useCallback } from 'react'
import { getAgents, getTasks, fetchAPI } from '@/lib/api'
import type { Task, Agent } from '@/types/api'

const STATUS_CONFIG: Record<string, { label: string; icon: string; color: string; bg: string }> = {
  pending:     { label: '待处理',     icon: '⏳', color: 'text-yellow-400',  bg: 'bg-yellow-500/5' },
  in_progress: { label: '进行中',     icon: '🔄', color: 'text-blue-400',   bg: 'bg-blue-500/5' },
  completed:   { label: '已完成',     icon: '✅', color: 'text-green-400',  bg: 'bg-green-500/5' },
  failed:      { label: '失败',       icon: '❌', color: 'text-red-400',    bg: 'bg-red-500/5' },
  cancelled:   { label: '已取消',     icon: '🚫', color: 'text-gray-400',  bg: 'bg-gray-500/5' },
}

const STATUS_ORDER = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']

function TaskCard({ task }: { task: Task }) {
  const cfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending

  return (
    <a
      href={`/tasks/${task.id}`}
      className="block bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-3 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/5"
    >
      {/* Header */}
      <div className="flex items-center gap-1.5 mb-2">
        <span className={`text-xs font-medium ${cfg.color}`}>{cfg.icon} {cfg.label}</span>
        <span className="text-[10px] text-[var(--muted)]">#{task.id}</span>
        {task.priority && task.priority !== 'medium' && (
          <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded ${
            task.priority === 'critical' ? 'bg-red-500/20 text-red-400' :
            task.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
            'bg-zinc-700 text-zinc-400'
          }`}>
            {task.priority === 'critical' ? '紧急' : task.priority === 'high' ? '高' : task.priority}
          </span>
        )}
      </div>

      {/* Title */}
      <p className="text-sm text-white mb-2 line-clamp-2">{task.title}</p>

      {/* Meta */}
      <div className="space-y-1">
        {task.agent_id && (
          <div className="text-[11px] text-[var(--muted)]">
            🤖 {task.agent_id}
          </div>
        )}
        {task.success_criteria && (
          <div className="text-[11px] text-[var(--muted)] truncate" title={task.success_criteria}>
            📐 {task.success_criteria}
          </div>
        )}
        {task.failure_reason && (
          <div className="text-[11px] text-red-400 truncate" title={task.failure_reason}>
            ❌ {task.failure_reason}
          </div>
        )}
        {task.created_at && (
          <div className="text-[10px] text-[var(--muted)]">
            {new Date(task.created_at).toLocaleString('zh-CN', {
              month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            })}
          </div>
        )}
      </div>
    </a>
  )
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  // Filters
  const [filterAgent, setFilterAgent] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')

  const loadData = useCallback(async () => {
    try {
      const params: Record<string, string> = {}
      if (filterAgent) params.agent_id = filterAgent
      if (filterStatus) params.status = filterStatus
      // Filter by priority client-side for simplicity
      const q = new URLSearchParams(params)
      const [tasksData, agentsData] = await Promise.all([
        fetchAPI<Task[]>(`/api/v1/tasks?${q}`),
        getAgents(),
      ])
      setTasks(tasksData)
      setAgents(agentsData)
    } catch (e) {
      console.error('Failed to load tasks', e)
    } finally {
      setLoading(false)
    }
  }, [filterAgent, filterStatus])

  useEffect(() => { loadData() }, [loadData])

  // Client-side priority filter
  const filtered = filterPriority
    ? tasks.filter(t => t.priority === filterPriority)
    : tasks

  // Group by status
  const columns = STATUS_ORDER.map(status => ({
    ...STATUS_CONFIG[status],
    status,
    tasks: filtered.filter(t => t.status === status),
  }))

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">📋 任务看板</h1>

      {/* ── Filters ── */}
      <div className="flex flex-wrap gap-3">
        {/* Agent filter */}
        <select
          value={filterAgent}
          onChange={e => { setFilterAgent(e.target.value); setLoading(true) }}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">🤖 所有 Agent</option>
          {agents.map(a => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>

        {/* Status filter */}
        <select
          value={filterStatus}
          onChange={e => { setFilterStatus(e.target.value); setLoading(true) }}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">📊 所有状态</option>
          {STATUS_ORDER.map(s => (
            <option key={s} value={s}>{STATUS_CONFIG[s].icon} {STATUS_CONFIG[s].label}</option>
          ))}
        </select>

        {/* Priority filter */}
        <select
          value={filterPriority}
          onChange={e => setFilterPriority(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">🏷️ 所有优先级</option>
          <option value="low">🟢 低</option>
          <option value="medium">🟡 中</option>
          <option value="high">🟠 高</option>
          <option value="critical">🔴 紧急</option>
        </select>

        <button
          onClick={() => { setFilterAgent(''); setFilterStatus(''); setFilterPriority(''); setLoading(true) }}
          className="px-3 py-1.5 text-sm text-[var(--muted)] hover:text-white transition-colors"
        >
          ↺ 重置
        </button>
      </div>

      {/* ── Kanban Board ── */}
      {loading ? (
        <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {columns.map(col => (
            <div key={col.status} className="min-h-[200px]">
              {/* Column Header */}
              <div className={`flex items-center justify-between mb-3 px-1`}>
                <h3 className={`text-sm font-medium ${col.color}`}>
                  {col.icon} {col.label}
                </h3>
                <span className="text-xs text-[var(--muted)] bg-zinc-800 px-2 py-0.5 rounded-full">
                  {col.tasks.length}
                </span>
              </div>

              {/* Cards */}
              <div className="space-y-2">
                {col.tasks.length === 0 ? (
                  <div className="text-xs text-[var(--muted)] text-center py-8 border border-dashed border-zinc-700 rounded-lg">
                    暂无任务
                  </div>
                ) : (
                  col.tasks.map(task => (
                    <TaskCard key={task.id} task={task} />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
