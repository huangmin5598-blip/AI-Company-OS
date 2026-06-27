'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

import {
  assignRealWorkbenchTask,
  clearRealWorkbenchTaskAssignment,
  createRealWorkbenchRun,
  listRealWorkbenchRuns,
  listRealWorkbenchTemplates,
} from '@/lib/realWorkbenchApi'
import type {
  RealWorkbenchExecutorSlot,
  RealWorkbenchRun,
  RealWorkbenchTask,
  RealWorkbenchTemplate,
} from '@/types/realWorkbench'

const names: Record<string, string> = {
  idea_to_prd_pilot: 'Idea-to-PRD 试点',
  spoken_agent_offer: '口播智能体方案',
  clip_matrix_agent: '混剪矩阵智能体',
}

const executors: Record<string, string> = {
  ceo_agent_slot: 'CEO Agent 建议槽位',
  codex_slot: 'Codex',
  claude_slot: 'Claude',
  hermes_slot: 'Hermes',
  openclaw_slot: 'OpenClaw',
  local_script_slot: 'local_script',
  manual_founder_slot: 'Founder 手动处理',
}

const assignmentSlots: RealWorkbenchExecutorSlot[] = [
  'codex_slot',
  'claude_slot',
  'hermes_slot',
  'openclaw_slot',
  'local_script_slot',
  'manual_founder_slot',
]

type Draft = {
  assigned_slot: RealWorkbenchExecutorSlot
  assignment_note: string
}

export default function RealWorkbenchPage() {
  const [templates, setTemplates] = useState<RealWorkbenchTemplate[]>([])
  const [runs, setRuns] = useState<RealWorkbenchRun[]>([])
  const [selected, setSelected] = useState<RealWorkbenchRun | null>(null)
  const [productLineId, setProductLineId] = useState('')
  const [founderGoal, setFounderGoal] = useState('')
  const [assignmentDrafts, setAssignmentDrafts] = useState<Record<string, Draft>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const [templateResult, runResult] = await Promise.all([
      listRealWorkbenchTemplates(),
      listRealWorkbenchRuns(),
    ])
    setTemplates(templateResult.templates)
    setRuns(runResult.runs)
    if (!productLineId && templateResult.templates[0]) {
      setProductLineId(templateResult.templates[0].product_line_id)
      setFounderGoal(templateResult.templates[0].default_goal)
    }
    if (selected) {
      const fresh = runResult.runs.find(run => run.run_id === selected.run_id)
      if (fresh) {
        setSelected(fresh)
        seedDrafts(fresh)
      }
    } else if (runResult.runs[0]) {
      setSelected(runResult.runs[0])
      seedDrafts(runResult.runs[0])
    }
  }, [productLineId, selected])

  useEffect(() => {
    refresh().catch(exc => setError(exc instanceof Error ? exc.message : String(exc)))
  }, [])

  async function createRun(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const run = await createRealWorkbenchRun({
        product_line_id: productLineId,
        founder_goal: founderGoal,
      })
      setSelected(run)
      seedDrafts(run)
      const list = await listRealWorkbenchRuns()
      setRuns(list.runs)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy(false)
    }
  }

  function seedDrafts(run: RealWorkbenchRun) {
    const next: Record<string, Draft> = {}
    for (const task of run.task_plan) {
      next[task.task_id] = {
        assigned_slot: task.assigned_slot || fallbackSlot(task),
        assignment_note: task.assignment_note || '',
      }
    }
    setAssignmentDrafts(next)
  }

  function fallbackSlot(task: RealWorkbenchTask): RealWorkbenchExecutorSlot {
    return assignmentSlots.includes(task.executor_slot as RealWorkbenchExecutorSlot)
      ? task.executor_slot as RealWorkbenchExecutorSlot
      : 'manual_founder_slot'
  }

  function updateDraft(taskId: string, patch: Partial<Draft>) {
    setAssignmentDrafts(current => ({
      ...current,
      [taskId]: {
        assigned_slot: current[taskId]?.assigned_slot || 'manual_founder_slot',
        assignment_note: current[taskId]?.assignment_note || '',
        ...patch,
      },
    }))
  }

  async function saveAssignment(task: RealWorkbenchTask) {
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      const draft = assignmentDrafts[task.task_id] || {
        assigned_slot: fallbackSlot(task),
        assignment_note: '',
      }
      const run = await assignRealWorkbenchTask(selected.run_id, task.task_id, draft)
      setSelected(run)
      seedDrafts(run)
      const list = await listRealWorkbenchRuns()
      setRuns(list.runs)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy(false)
    }
  }

  async function clearAssignment(task: RealWorkbenchTask) {
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      const run = await clearRealWorkbenchTaskAssignment(selected.run_id, task.task_id)
      setSelected(run)
      seedDrafts(run)
      const list = await listRealWorkbenchRuns()
      setRuns(list.runs)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
              Founder Control Center Real Workbench · RS1-B
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              多产品线真实工作台基础版
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-zinc-300">
              Founder 输入目标后，系统把目标拆成产品线任务计划并保存到 pilot DB。
              本页支持手动指定接单槽位，但不会调用真实 Codex / Claude / OpenClaw / local_script，
              不启用调度器，也不是生产权威。
            </p>
          </div>
          <Link href="/vs001" className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-200">
            返回 VS-001
          </Link>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Boundary label="权威边界" value="pilot_non_authoritative" />
          <Boundary label="执行状态" value="未调用真实执行者" />
          <Boundary label="调度状态" value="仅手动派工意图" />
          <Boundary label="公开状态" value="restricted / 非 public-safe" />
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <section className="space-y-4">
          <form onSubmit={createRun} className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-5">
            <h2 className="font-medium text-white">创建持久化 run</h2>
            <div className="mt-4 space-y-2">
              {templates.map(template => (
                <button
                  key={template.product_line_id}
                  type="button"
                  onClick={() => {
                    setProductLineId(template.product_line_id)
                    setFounderGoal(template.default_goal)
                  }}
                  className={`w-full rounded-lg border p-3 text-left ${
                    productLineId === template.product_line_id
                      ? 'border-emerald-400 bg-emerald-500/10'
                      : 'border-zinc-800 bg-zinc-950/50 hover:border-zinc-600'
                  }`}
                >
                  <div className="font-medium text-white">
                    {names[template.product_line_id] || template.display_name}
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">{template.task_count} 个计划任务</div>
                </button>
              ))}
            </div>
            <label className="mt-4 block text-xs text-zinc-400">
              Founder 目标
              <textarea
                value={founderGoal}
                onChange={event => setFounderGoal(event.target.value)}
                rows={5}
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
              />
            </label>
            <button
              disabled={busy || !productLineId}
              className="mt-4 w-full rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              创建 run
            </button>
          </form>

          <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium text-white">已保存 runs</h2>
              <button onClick={() => refresh().catch(exc => setError(String(exc)))} className="text-xs text-blue-300">
                刷新
              </button>
            </div>
            <div className="space-y-2">
              {runs.map(run => (
                <button
                  key={run.run_id}
                  onClick={() => {
                    setSelected(run)
                    seedDrafts(run)
                  }}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 text-left hover:border-zinc-600"
                >
                  <div className="truncate text-sm text-white">
                    {names[run.product_line.product_line_id] || run.product_line.display_name}
                  </div>
                  <div className="mt-1 truncate text-xs text-zinc-500">{run.founder_goal}</div>
                </button>
              ))}
              {!runs.length && <p className="text-sm text-zinc-500">还没有持久化 run。</p>}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-6">
          {!selected ? (
            <div className="flex min-h-96 items-center justify-center text-zinc-500">
              创建或选择一个 run。
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  {names[selected.product_line.product_line_id] || selected.product_line.display_name}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">{selected.founder_goal}</p>
                <p className="mt-2 break-all text-xs text-zinc-600">{selected.run_id}</p>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <Boundary label="状态" value={selected.status} />
                <Boundary label="模式" value={selected.mode} />
                <Boundary label="任务哈希" value={selected.task_plan_hash} />
              </div>
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-zinc-300">任务计划</h3>
                {selected.task_plan.map(task => (
                  <div key={task.task_id} className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-medium text-white">{task.title}</div>
                      <span className="text-xs text-emerald-300">
                        {assignmentLabel(task.assignment_status)}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-zinc-500">
                      第 {task.step_index} 步 · 建议：{executors[task.executor_slot] || task.executor_slot}
                    </div>
                    <p className="mt-3 text-sm text-zinc-400">{task.expected_output}</p>
                    <div className="mt-4 rounded-lg border border-zinc-800 bg-black/20 p-3">
                      <div className="grid gap-3 md:grid-cols-[180px_1fr_auto]">
                        <label className="text-xs text-zinc-400">
                          派给
                          <select
                            value={assignmentDrafts[task.task_id]?.assigned_slot || task.assigned_slot || fallbackSlot(task)}
                            onChange={event => updateDraft(task.task_id, {
                              assigned_slot: event.target.value as RealWorkbenchExecutorSlot,
                            })}
                            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-2 text-sm text-white"
                          >
                            {assignmentSlots.map(slot => (
                              <option key={slot} value={slot}>{executors[slot]}</option>
                            ))}
                          </select>
                        </label>
                        <label className="text-xs text-zinc-400">
                          派工备注
                          <input
                            value={assignmentDrafts[task.task_id]?.assignment_note ?? task.assignment_note}
                            onChange={event => updateDraft(task.task_id, {
                              assignment_note: event.target.value,
                            })}
                            placeholder="例如：先由 Codex 起草，再由 Founder 复核"
                            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500"
                          />
                        </label>
                        <div className="flex items-end gap-2">
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => saveAssignment(task)}
                            className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                          >
                            保存
                          </button>
                          <button
                            type="button"
                            disabled={busy || task.assignment_status === 'unassigned'}
                            onClick={() => clearAssignment(task)}
                            className="rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 hover:border-zinc-500 disabled:opacity-50"
                          >
                            清除
                          </button>
                        </div>
                      </div>
                      <div className="mt-3 text-xs text-zinc-500">
                        当前派工：
                        {task.assigned_slot
                          ? `${executors[task.assigned_slot] || task.assigned_slot} · ${task.assigned_by || 'unknown'}`
                          : '尚未派工'}
                        。这只是 pilot 手动派工意图，不会触发真实执行。
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function assignmentLabel(status: RealWorkbenchTask['assignment_status']) {
  if (status === 'assigned') return '已派工'
  if (status === 'revised') return '已调整派工'
  return '待派工'
}

function Boundary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-700 bg-black/20 px-3 py-2">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 break-all text-xs font-medium text-zinc-200">{value}</div>
    </div>
  )
}
