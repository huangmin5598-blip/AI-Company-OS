'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

import {
  createRealWorkbenchRun,
  listRealWorkbenchRuns,
  listRealWorkbenchTemplates,
} from '@/lib/realWorkbenchApi'
import type {
  RealWorkbenchRun,
  RealWorkbenchTemplate,
} from '@/types/realWorkbench'

const names: Record<string, string> = {
  idea_to_prd_pilot: 'Idea-to-PRD 试点',
  spoken_agent_offer: '口播智能体方案',
  clip_matrix_agent: '混剪矩阵智能体',
}

const executors: Record<string, string> = {
  ceo_agent_slot: 'CEO Agent 槽位',
  codex_slot: 'Codex 槽位',
  claude_slot: 'Claude 槽位',
  local_script_slot: 'local_script 槽位',
}

export default function RealWorkbenchPage() {
  const [templates, setTemplates] = useState<RealWorkbenchTemplate[]>([])
  const [runs, setRuns] = useState<RealWorkbenchRun[]>([])
  const [selected, setSelected] = useState<RealWorkbenchRun | null>(null)
  const [productLineId, setProductLineId] = useState('')
  const [founderGoal, setFounderGoal] = useState('')
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
      if (fresh) setSelected(fresh)
    } else if (runResult.runs[0]) {
      setSelected(runResult.runs[0])
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
              Founder Control Center Real Workbench · RS1-A
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              多产品线真实工作台基础版
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-zinc-300">
              Founder 输入目标后，系统把目标拆成产品线任务计划并保存到 pilot DB。
              本页不调用真实 Codex / Claude / OpenClaw / local_script，不启用 scheduler，
              也不是 operational authority。
            </p>
          </div>
          <Link href="/vs001" className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-200">
            返回 VS-001
          </Link>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Boundary label="权威边界" value="pilot_non_authoritative" />
          <Boundary label="执行状态" value="未调用真实执行者" />
          <Boundary label="调度状态" value="未启用 scheduler" />
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
                  onClick={() => setSelected(run)}
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
                      <span className="text-xs text-emerald-300">已规划</span>
                    </div>
                    <div className="mt-1 text-xs text-zinc-500">
                      Step {task.step_index} · {executors[task.executor_slot] || task.executor_slot}
                    </div>
                    <p className="mt-3 text-sm text-zinc-400">{task.expected_output}</p>
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

function Boundary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-700 bg-black/20 px-3 py-2">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 break-all text-xs font-medium text-zinc-200">{value}</div>
    </div>
  )
}
