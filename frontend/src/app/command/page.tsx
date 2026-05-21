'use client'

import { useEffect, useState, useCallback } from 'react'
import { getAgents, getTasks, sendCommand } from '@/lib/api'
import type { Agent, Task } from '@/types/api'

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  in_progress: '进行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-yellow-400',
  in_progress: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  cancelled: 'text-gray-400',
}

const STATUS_ICONS: Record<string, string> = {
  pending: '⏳',
  in_progress: '🔄',
  completed: '✅',
  failed: '❌',
  cancelled: '🚫',
}

export default function CommandPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)

  // Command form
  const [agentId, setAgentId] = useState('main')
  const [instruction, setInstruction] = useState('')
  const [priority, setPriority] = useState('medium')
  const [requiredSkills, setRequiredSkills] = useState('')
  const [successCriteria, setSuccessCriteria] = useState('')

  // Load agents and tasks
  const loadData = useCallback(async () => {
    try {
      const [agentsData, tasksData] = await Promise.all([
        getAgents(),
        getTasks({ limit: 20 }),
      ])
      setAgents(agentsData)
      setTasks(tasksData)
      if (agentsData.length > 0 && agentId === 'main') {
        // Default to first agent if 'main' not found
        const mainExists = agentsData.find(a => a.id === 'main')
        if (!mainExists) setAgentId(agentsData[0].id)
      }
    } catch (e) {
      console.error('Failed to load data', e)
    } finally {
      setLoading(false)
    }
  }, [agentId])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Poll for in-progress tasks every 5 seconds
  useEffect(() => {
    const hasInProgress = tasks.some(t => t.status === 'in_progress')
    if (!hasInProgress) return

    const interval = setInterval(async () => {
      try {
        const freshTasks = await getTasks({ limit: 20 })
        setTasks(freshTasks)
      } catch (e) {
        // Silent fail on poll
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [tasks])

  // Send command
  const handleSend = async () => {
    if (!instruction.trim()) return

    setSending(true)
    setResult(null)

    try {
      const resp = await sendCommand({
        instruction: instruction.trim(),
        agent_id: agentId,
        priority,
        required_skills: requiredSkills || null,
        success_criteria: successCriteria || null,
      })
      setResult({ ok: true, message: resp.message })
      setInstruction('')

      // Refresh task list
      const freshTasks = await getTasks({ limit: 20 })
      setTasks(freshTasks)
    } catch (e: any) {
      setResult({ ok: false, message: e.message || '发送失败' })
    } finally {
      setSending(false)
    }
  }

  // Detect skill gap
  const selectedAgent = agents.find(a => a.id === agentId)
  const agentSkills: string[] = selectedAgent?.skills
    ? JSON.parse(selectedAgent.skills)
    : []
  const requestedSkills: string[] = requiredSkills
    ? requiredSkills.split(',').map(s => s.trim()).filter(Boolean)
    : []
  const missingSkills = requestedSkills.filter(
    s => !agentSkills.some(as => as.toLowerCase().includes(s.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">🎙️ 指挥台</h1>

      {/* ── Command Form ── */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Agent Selector */}
          <div>
            <label className="block text-xs text-[var(--muted)] mb-1">目标 Agent</label>
            <select
              value={agentId}
              onChange={e => setAgentId(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white"
            >
              {agents.map(a => (
                <option key={a.id} value={a.id}>
                  {a.name} {a.model ? `(${a.model})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs text-[var(--muted)] mb-1">优先级</label>
            <select
              value={priority}
              onChange={e => setPriority(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white"
            >
              <option value="low">🟢 低</option>
              <option value="medium">🟡 中</option>
              <option value="high">🟠 高</option>
              <option value="critical">🔴 紧急</option>
            </select>
          </div>

          {/* Skills Display */}
          <div>
            <label className="block text-xs text-[var(--muted)] mb-1">Agent 已有技能</label>
            <div className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-[var(--muted)] min-h-[38px]">
              {agentSkills.length > 0
                ? agentSkills.join(', ')
                : '未配置技能'}
            </div>
          </div>
        </div>

        {/* Instruction */}
        <div className="mb-4">
          <label className="block text-xs text-[var(--muted)] mb-1">指令内容</label>
          <textarea
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            placeholder="例如：去研究一下xx市场，明天汇报"
            rows={3}
            className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 resize-none"
          />
        </div>

        {/* Advanced fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs text-[var(--muted)] mb-1">所需技能（逗号分隔）</label>
            <input
              value={requiredSkills}
              onChange={e => setRequiredSkills(e.target.value)}
              placeholder="research, writing, analysis"
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--muted)] mb-1">验收标准</label>
            <input
              value={successCriteria}
              onChange={e => setSuccessCriteria(e.target.value)}
              placeholder="报告 > 2000 字，3 个数据来源"
              className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500"
            />
          </div>
        </div>

        {/* Skill gap warning */}
        {missingSkills.length > 0 && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
            ⚠️ 技能缺口：Agent <strong>{agentId}</strong> 缺少以下技能：
            {missingSkills.map(s => (
              <span key={s} className="inline-block ml-2 px-2 py-0.5 bg-red-500/20 rounded text-red-300 text-xs">
                {s}
              </span>
            ))}
          </div>
        )}

        {/* Result message */}
        {result && (
          <div className={`mb-4 p-3 rounded text-sm ${
            result.ok
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}>
            {result.ok ? '✅ ' : '❌ '}{result.message}
          </div>
        )}

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={sending || !instruction.trim()}
          className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {sending ? '🚀 发送中...' : '🚀 发送指令'}
        </button>
      </div>

      {/* ── Execution History ── */}
      <div>
        <h2 className="text-lg font-medium text-white mb-3">📋 执行记录</h2>
        {loading ? (
          <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
        ) : tasks.length === 0 ? (
          <div className="text-sm text-[var(--muted)]">暂无执行记录</div>
        ) : (
          <div className="space-y-2">
            {tasks.map(task => (
              <div
                key={task.id}
                className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 hover:border-blue-500/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={STATUS_COLORS[task.status] || 'text-gray-400'}>
                        {STATUS_ICONS[task.status] || '❓'} {STATUS_LABELS[task.status] || task.status}
                      </span>
                      <span className="text-xs text-[var(--muted)]">
                        #{task.id}
                      </span>
                      {task.agent_id && (
                        <span className="text-xs px-1.5 py-0.5 bg-zinc-700 rounded text-[var(--muted)]">
                          {task.agent_id}
                        </span>
                      )}
                      {task.priority && task.priority !== 'medium' && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          task.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
                          task.priority === 'critical' ? 'bg-red-500/20 text-red-400' :
                          'bg-zinc-700 text-zinc-400'
                        }`}>
                          {task.priority}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-white truncate">{task.title}</p>

                    {/* Details expandable on click */}
                    {(task.success_criteria || task.required_skills || task.failure_reason) && (
                      <div className="mt-2 space-y-1">
                        {task.success_criteria && (
                          <div className="text-xs text-[var(--muted)]">
                            📐 验收标准：{task.success_criteria}
                          </div>
                        )}
                        {task.required_skills && (
                          <div className="text-xs text-[var(--muted)]">
                            🛠️ 所需技能：{task.required_skills}
                          </div>
                        )}
                        {task.failure_reason && (
                          <div className="text-xs text-red-400">
                            ❌ 失败原因：{task.failure_reason}
                          </div>
                        )}
                        {task.error_message && (
                          <div className="text-xs text-red-400/70 truncate">
                            {task.error_message}
                          </div>
                        )}
                        {task.result_summary && (
                          <div className="text-xs text-green-400/70 truncate">
                            📊 {task.result_summary}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Timestamp */}
                  <div className="text-xs text-[var(--muted)] whitespace-nowrap shrink-0">
                    {task.created_at ? new Date(task.created_at).toLocaleString('zh-CN', {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
