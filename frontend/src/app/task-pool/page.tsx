'use client'

import { useEffect, useState, useCallback } from 'react'
import { getTaskPool } from '@/lib/api'
import type { TaskPoolItem } from '@/types/api'

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
  alert: '🔔',
  command: '⚡',
  manual: '✏️',
  cron: '⏰',
}

const PRIORITY_PILL: Record<string, { label: string; color: string }> = {
  critical: { label: '🔴 紧急', color: 'bg-red-500/20 text-red-400' },
  high:     { label: '🟠 高',   color: 'bg-orange-500/20 text-orange-400' },
  medium:   { label: '🟡 中',   color: 'bg-yellow-500/20 text-yellow-400' },
  low:      { label: '🟢 低',   color: 'bg-green-500/20 text-green-400' },
}

const STATUS_OPTIONS = Object.keys(STATUS_MAP)

function TaskCard({ task }: { task: TaskPoolItem }) {
  const cfg = STATUS_MAP[task.status] || STATUS_MAP.draft
  const srcIcon = SOURCE_ICON[task.source] || '📋'
  const pri = PRIORITY_PILL[task.priority] || PRIORITY_PILL.medium

  return (
    <a
      href={`/task-pool/${task.id}`}
      className="block bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/5"
    >
      {/* Header row: status badge + source icon */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.color} ${cfg.bg}`}>
          {cfg.label}
        </span>
        <span className="text-sm" title={task.source}>{srcIcon}</span>
      </div>

      {/* Title */}
      <p className="text-sm text-white mb-3 line-clamp-2 font-medium">{task.title}</p>

      {/* Tags row */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${pri.color} ${pri.color.replace('text-', 'bg-').replace('400', '500/20')}`}>
          {pri.label}
        </span>
        {task.business_line && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-700/50 text-zinc-300">
            {task.business_line}
          </span>
        )}
      </div>

      {/* Meta */}
      <div className="space-y-1">
        {task.assigned_agent && (
          <div className="text-[11px] text-[var(--muted)]">
            🤖 {task.assigned_agent}
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

export default function TaskPoolPage() {
  const [tasks, setTasks] = useState<TaskPoolItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [filterStatus, setFilterStatus] = useState('')
  const [filterBusinessLine, setFilterBusinessLine] = useState('')
  const [filterSource, setFilterSource] = useState('')
  const [filterPriority, setFilterPriority] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: { status?: string; business_line?: string; source?: string; priority?: string } = {}
      if (filterStatus) params.status = filterStatus
      if (filterBusinessLine) params.business_line = filterBusinessLine
      if (filterSource) params.source = filterSource
      if (filterPriority) params.priority = filterPriority
      const data = await getTaskPool(params)
      setTasks(data)
    } catch (e) {
      setError('加载任务池失败，请确认 API 服务已启动')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterBusinessLine, filterSource, filterPriority])

  useEffect(() => { loadData() }, [loadData])

  return (
    <div className="space-y-4">
      {/* Header */}
      <h1 className="text-xl font-semibold text-white">
        📋 TASK-POOL 任务总览
        {!loading && <span className="ml-2 text-sm text-[var(--muted)] font-normal">({tasks.length})</span>}
      </h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">📊 所有状态</option>
          {STATUS_OPTIONS.map(s => (
            <option key={s} value={s}>{STATUS_MAP[s].label}</option>
          ))}
        </select>

        <select
          value={filterSource}
          onChange={e => setFilterSource(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">📋 所有来源</option>
          <option value="alert">🔔 告警</option>
          <option value="command">⚡ 指令</option>
          <option value="manual">✏️ 手动</option>
          <option value="cron">⏰ 定时</option>
        </select>

        <select
          value={filterPriority}
          onChange={e => setFilterPriority(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="">🏷️ 所有优先级</option>
          <option value="critical">🔴 紧急</option>
          <option value="high">🟠 高</option>
          <option value="medium">🟡 中</option>
          <option value="low">🟢 低</option>
        </select>

        <input
          type="text"
          placeholder="业务线..."
          value={filterBusinessLine}
          onChange={e => setFilterBusinessLine(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-white w-32"
        />

        <button
          onClick={() => { setFilterStatus(''); setFilterBusinessLine(''); setFilterSource(''); setFilterPriority('') }}
          className="px-3 py-1.5 text-sm text-[var(--muted)] hover:text-white transition-colors"
        >
          ↺ 重置
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
      ) : error ? (
        <div className="text-red-400 text-sm">⚠️ {error}</div>
      ) : tasks.length === 0 ? (
        <div className="text-sm text-[var(--muted)] text-center py-16 border border-dashed border-zinc-700 rounded-lg">
          暂无任务。系统正在监听告警，发现失败将自动创建任务。
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map(task => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  )
}
