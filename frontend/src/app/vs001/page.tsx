'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

import {
  approvePilotWorkOrder,
  createPilotWorkOrder,
  executePilotWorkOrder,
  listPilotWorkOrders,
  pilotStatus,
  requestPilotApproval,
  reviewPilotWorkOrder,
} from '@/lib/vs001Api'
import type { PilotStatus, WorkOrderEnvelope } from '@/types/vs001'

const stateTone: Record<string, string> = {
  draft: 'text-zinc-300 border-zinc-600',
  waiting_approval: 'text-amber-300 border-amber-600/60',
  queued: 'text-blue-300 border-blue-600/60',
  running: 'text-violet-300 border-violet-600/60',
  waiting_review: 'text-fuchsia-300 border-fuchsia-600/60',
  done: 'text-emerald-300 border-emerald-600/60',
}

export default function Vs001PilotPage() {
  const [status, setStatus] = useState<PilotStatus | null>(null)
  const [orders, setOrders] = useState<WorkOrderEnvelope[]>([])
  const [selected, setSelected] = useState<WorkOrderEnvelope | null>(null)
  const [result, setResult] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    skill_id: 'vs001.echo-markdown',
    task_type: 'render_markdown',
    input_context: 'Create one truthful local pilot result.',
    expected_output: 'A reviewed Markdown document.',
  })

  const refresh = useCallback(async () => {
    const [pilot, list] = await Promise.all([
      pilotStatus(),
      listPilotWorkOrders(),
    ])
    setStatus(pilot)
    setOrders(list.work_orders)
    if (selected) {
      const fresh = list.work_orders.find(
        order => order.data.work_order_id === selected.data.work_order_id,
      )
      if (fresh) setSelected({ ...selected, ...fresh })
    }
  }, [selected])

  useEffect(() => {
    refresh().catch(exc => setError(String(exc)))
  }, [])

  async function run(label: string, action: () => Promise<WorkOrderEnvelope>) {
    setBusy(label)
    setError('')
    try {
      const value = await action()
      setSelected(value)
      if (value.execution?.result_markdown) {
        setResult(value.execution.result_markdown)
      }
      await refresh()
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy('')
    }
  }

  async function create(event: FormEvent) {
    event.preventDefault()
    await run('create', () => createPilotWorkOrder(form))
  }

  const state = selected?.data.canonical_state
  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-300">
              VS-001 Truthful Local WorkOrder Loop
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              Local Pilot / OS-Governed / Non-production / Not Operational Authority
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-zinc-300">
              Approval、execution 和 Review 是三个独立动作。Controlled Builtin
              成功只会进入 waiting_review，只有 Founder 明确 Review 后才能 done。
              Review passed 只创建 restricted Asset Candidate，Asset Approval
              仍是另一个独立动作。
            </p>
          </div>
          <div className="rounded-lg border border-zinc-700 bg-black/20 px-4 py-3 text-xs">
            <div className="text-zinc-400">Operational DB protection</div>
            <div className={status == null ? 'text-zinc-400' : status.operational_database.matches ? 'text-emerald-300' : 'text-red-300'}>
              {status == null
                ? 'CHECKING'
                : status.operational_database.matches
                  ? 'SHA-256 MATCH'
                  : 'HASH MISMATCH'}
            </div>
            <div className="mt-1 max-w-64 break-all text-zinc-500">
              {status?.operational_database.actual_sha256 || 'checking...'}
            </div>
          </div>
        </div>
        <div className="mt-5 rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-blue-100">
                Founder Control Center Demo Spine
              </div>
              <p className="mt-1 max-w-3xl text-xs text-blue-100/70">
                Run 2-3 product-line offers side by side as a pilot-only replay:
                Founder goal → CEO decomposition → Work Queue → simulated executor
                slots → Audit Packet → restricted Asset → Go / No-Go.
              </p>
            </div>
            <Link
              href="/vs001/demo-spine"
              className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-400"
            >
              Open Demo Spine
            </Link>
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <section className="space-y-4">
          <form onSubmit={create} className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-5">
            <h2 className="font-medium text-white">Create canonical draft</h2>
            <div className="mt-4 space-y-3">
              {([
                ['skill_id', 'Skill ID'],
                ['task_type', 'Task type'],
                ['input_context', 'Input context'],
                ['expected_output', 'Expected output'],
              ] as const).map(([key, label]) => (
                <label key={key} className="block text-xs text-zinc-400">
                  {label}
                  <textarea
                    value={form[key]}
                    onChange={event => setForm({ ...form, [key]: event.target.value })}
                    rows={key === 'input_context' ? 3 : 1}
                    className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
                  />
                </label>
              ))}
            </div>
            <button
              disabled={Boolean(busy)}
              className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
            >
              Create draft
            </button>
          </form>

          <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium text-white">Pilot WorkOrders</h2>
              <button onClick={() => refresh()} className="text-xs text-blue-400">
                Refresh
              </button>
            </div>
            <div className="space-y-2">
              {orders.map(order => (
                <button
                  key={order.data.work_order_id}
                  onClick={() => setSelected(order)}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 text-left hover:border-zinc-600"
                >
                  <div className="truncate text-sm text-white">{order.data.task_type}</div>
                  <div className="mt-1 flex items-center justify-between text-xs">
                    <span className="truncate text-zinc-500">{order.data.work_order_id}</span>
                    <span className="text-zinc-300">{order.data.canonical_state}</span>
                  </div>
                </button>
              ))}
              {!orders.length && <p className="text-sm text-zinc-500">No pilot WorkOrders yet.</p>}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-6">
          {!selected ? (
            <div className="flex min-h-96 items-center justify-center text-zinc-500">
              Create or select a WorkOrder.
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="text-xl font-semibold text-white">{selected.data.task_type}</h2>
                  <span className={`rounded-full border px-2.5 py-1 text-xs ${stateTone[state || ''] || 'border-zinc-600 text-zinc-300'}`}>
                    {state}
                  </span>
                </div>
                <p className="mt-2 break-all text-xs text-zinc-500">{selected.data.work_order_id}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Info label="Authority" value={selected.governance?.authority || selected.provenance.authority} />
                <Info label="Row version" value={String(selected.data.row_version)} />
                <Info label="Approval" value={selected.latest_approval?.decision || 'not requested'} />
                <Info label="Review" value={selected.latest_review?.state || 'not requested'} />
              </div>

              <div className="flex flex-wrap gap-3 border-y border-zinc-800 py-5">
                <Action
                  label="1. Request Approval"
                  disabled={state !== 'draft' || Boolean(busy)}
                  onClick={() => run('request', () => requestPilotApproval(selected.data.work_order_id))}
                />
                <Action
                  label="2. Approve"
                  disabled={state !== 'waiting_approval' || Boolean(busy)}
                  onClick={() => run('approve', () => approvePilotWorkOrder(selected.data.work_order_id))}
                />
                <Action
                  label="3. Execute Builtin"
                  disabled={state !== 'queued' || Boolean(busy)}
                  onClick={() => run('execute', () => executePilotWorkOrder(
                    selected.data.work_order_id,
                    { heading: selected.data.task_type, body: selected.data.input_context },
                  ))}
                />
                <Action
                  label="4. Review Passed"
                  disabled={state !== 'waiting_review' || Boolean(busy)}
                  onClick={() => run('review', () => reviewPilotWorkOrder(selected.data.work_order_id))}
                />
              </div>

              <div>
                <h3 className="text-sm font-medium text-zinc-300">Result evidence</h3>
                <pre className="mt-2 min-h-48 whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm text-zinc-300">
                  {result || 'Execution output will appear here. Review remains a separate action.'}
                </pre>
              </div>

              <div>
                <h3 className="text-sm font-medium text-zinc-300">
                  Pilot Assets
                </h3>
                <div className="mt-2 space-y-2">
                  {(selected.assets || []).map(asset => (
                    <Link
                      key={asset.asset_id}
                      href={`/vs001/assets/${asset.asset_id}`}
                      className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-blue-500/50"
                    >
                      <span>
                        <span className="block text-sm text-white">{asset.title}</span>
                        <span className="block text-xs text-zinc-500">
                          Restricted / Pilot / Not public-safe
                        </span>
                      </span>
                      <span className="text-xs text-blue-300">{asset.status}</span>
                    </Link>
                  ))}
                  {!selected.assets?.length && (
                    <p className="text-sm text-zinc-500">
                      A passed Review will create an Asset Candidate.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-sm text-zinc-200">{value}</div>
    </div>
  )
}

function Action({
  label,
  disabled,
  onClick,
}: {
  label: string
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded-lg border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm text-blue-300 hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600"
    >
      {label}
    </button>
  )
}
