'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getTask, getTaskMessages } from '@/lib/api'
import type { Task, TaskMessage } from '@/types/api'

const STATUS_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  pending:     { label: '待处理',     icon: '⏳', color: 'text-yellow-400' },
  in_progress: { label: '进行中',     icon: '🔄', color: 'text-blue-400' },
  completed:   { label: '已完成',     icon: '✅', color: 'text-green-400' },
  failed:      { label: '失败',       icon: '❌', color: 'text-red-400' },
  cancelled:   { label: '已取消',     icon: '🚫', color: 'text-gray-400' },
}

function InfoRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex justify-between py-2 border-b border-zinc-800 last:border-0">
      <span className="text-sm text-[var(--muted)]">{label}</span>
      <span className={`text-sm ${color || 'text-white'} text-right max-w-[60%]`}>{value}</span>
    </div>
  )
}

export default function TaskDetailPage() {
  const params = useParams()
  const taskId = Number(params.id)
  const [task, setTask] = useState<Task | null>(null)
  const [messages, setMessages] = useState<TaskMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!taskId) return
    Promise.all([
      getTask(taskId),
      getTaskMessages(taskId),
    ]).then(([t, msgs]) => {
      setTask(t)
      setMessages(msgs)
    }).catch(e => {
      setError(e.message)
    }).finally(() => {
      setLoading(false)
    })
  }, [taskId])

  // Poll for updates if in progress
  useEffect(() => {
    if (!task || task.status !== 'in_progress') return
    const interval = setInterval(async () => {
      try {
        const [t, msgs] = await Promise.all([
          getTask(taskId),
          getTaskMessages(taskId),
        ])
        setTask(t)
        setMessages(msgs)
      } catch { /* silent */ }
    }, 5000)
    return () => clearInterval(interval)
  }, [task, taskId])

  if (loading) {
    return <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
  }

  if (error || !task) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">😵</div>
        <div className="text-sm text-red-400">{error || '任务不存在'}</div>
        <a href="/tasks" className="mt-4 inline-block text-sm text-blue-400 hover:text-blue-300">
          ← 返回看板
        </a>
      </div>
    )
  }

  const cfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending
  const priorityLabel: Record<string, string> = {
    low: '🟢 低', medium: '🟡 中', high: '🟠 高', critical: '🔴 紧急',
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="text-sm text-[var(--muted)]">
        <a href="/tasks" className="hover:text-white transition-colors">📋 任务看板</a>
        <span className="mx-2">/</span>
        <span className="text-white">#{task.id}</span>
      </div>

      {/* ── Task Header ── */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <span className={`text-lg ${cfg.color}`}>{cfg.icon}</span>
          <h1 className="text-lg font-semibold text-white flex-1">{task.title}</h1>
          {task.status === 'failed' && (
            <span className="px-2 py-1 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
              失败
            </span>
          )}
        </div>

        {/* Description */}
        {task.description && (
          <p className="text-sm text-gray-300 mb-4 whitespace-pre-wrap">{task.description}</p>
        )}

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-x-6">
          <InfoRow label="状态" value={`${cfg.icon} ${cfg.label}`} color={cfg.color} />
          <InfoRow label="优先级" value={priorityLabel[task.priority] || task.priority} />
          <InfoRow label="Agent" value={task.agent_id} />
          <InfoRow label="来源" value={task.source || '-'} />
          <InfoRow
            label="创建时间"
            value={task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-'}
          />
          <InfoRow
            label="更新时间"
            value={task.updated_at ? new Date(task.updated_at).toLocaleString('zh-CN') : '-'}
          />
        </div>
      </div>

      {/* ── Success Criteria & Skills ── */}
      {(task.success_criteria || task.required_skills) && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
          <h2 className="text-sm font-medium text-white mb-3">📋 任务要求</h2>
          {task.success_criteria && (
            <div className="mb-3">
              <div className="text-xs text-[var(--muted)] mb-1">验收标准</div>
              <div className="text-sm text-white bg-zinc-800 rounded px-3 py-2">
                {task.success_criteria}
              </div>
            </div>
          )}
          {task.required_skills && (
            <div>
              <div className="text-xs text-[var(--muted)] mb-1">所需技能</div>
              <div className="flex flex-wrap gap-1.5">
                {(JSON.parse(task.required_skills) as string[]).map((s: string) => (
                  <span key={s} className="px-2 py-1 bg-blue-500/10 border border-blue-500/30 rounded text-xs text-blue-400">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Failure Analysis Card ── */}
      {task.status === 'failed' && (task.failure_reason || task.error_message) && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-6">
          <h2 className="text-sm font-medium text-red-400 mb-3">❌ 失败原因分析</h2>
          {task.failure_reason && (
            <div className="mb-3">
              <div className="text-xs text-red-400/70 mb-1">失败原因</div>
              <div className="text-sm text-red-300 bg-red-500/10 rounded px-3 py-2 font-mono">
                {task.failure_reason}
              </div>
            </div>
          )}
          {task.error_message && (
            <div>
              <div className="text-xs text-red-400/70 mb-1">错误详情</div>
              <pre className="text-xs text-red-300/70 bg-red-500/10 rounded px-3 py-2 overflow-x-auto whitespace-pre-wrap font-mono">
                {task.error_message}
              </pre>
            </div>
          )}
          <div className="mt-4 p-3 bg-zinc-800/50 rounded text-xs text-[var(--muted)]">
            💡 建议：检查错误信息后，可以回到 <a href="/command" className="text-blue-400 hover:text-blue-300">指挥台</a> 重新发送指令，或尝试降低任务复杂度。
          </div>
        </div>
      )}

      {/* ── Result Summary ── */}
      {task.result_summary && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
          <h2 className="text-sm font-medium text-white mb-3">📊 执行结果</h2>
          <div className="text-sm text-gray-300 whitespace-pre-wrap">{task.result_summary}</div>
        </div>
      )}

      {/* ── Execution Log ── */}
      {messages.length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
          <h2 className="text-sm font-medium text-white mb-3">💬 执行日志</h2>
          <div className="space-y-2">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`rounded-lg p-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-500/5 border border-blue-500/20'
                    : msg.role === 'agent'
                    ? 'bg-green-500/5 border border-green-500/20'
                    : 'bg-zinc-800/50 border border-zinc-700/30'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-medium ${
                    msg.role === 'user'
                      ? 'text-blue-400'
                      : msg.role === 'agent'
                      ? 'text-green-400'
                      : 'text-gray-400'
                  }`}>
                    {msg.role === 'user' ? '🧑 用户' : msg.role === 'agent' ? '🤖 Agent' : '⚙️ 系统'}
                  </span>
                  {msg.created_at && (
                    <span className="text-[10px] text-[var(--muted)]">
                      {new Date(msg.created_at).toLocaleString('zh-CN', {
                        hour: '2-digit', minute: '2-digit', second: '2-digit'
                      })}
                    </span>
                  )}
                </div>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-sans">
                  {msg.content}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
