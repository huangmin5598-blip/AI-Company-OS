'use client'

import Link from 'next/link'
import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  advanceDemoRun,
  createDemoRun,
  decideDemoRun,
  listDemoOffers,
  listDemoRuns,
} from '@/lib/demoSpineApi'
import type { DemoOffer, DemoRun, DemoTaskStatus } from '@/types/demoSpine'

const statusTone: Record<string, string> = {
  planned: 'border-zinc-700 text-zinc-300',
  active: 'border-blue-500/50 text-blue-300',
  ready_for_decision: 'border-amber-500/60 text-amber-300',
  go: 'border-emerald-500/60 text-emerald-300',
  no_go: 'border-red-500/60 text-red-300',
}

const taskTone: Record<DemoTaskStatus, string> = {
  planned: 'bg-zinc-900 text-zinc-400',
  queued: 'bg-blue-500/10 text-blue-300',
  running: 'bg-violet-500/10 text-violet-300',
  waiting_review: 'bg-fuchsia-500/10 text-fuchsia-300',
  done: 'bg-emerald-500/10 text-emerald-300',
}

export default function DemoSpinePage() {
  const [offers, setOffers] = useState<DemoOffer[]>([])
  const [runs, setRuns] = useState<DemoRun[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [offerId, setOfferId] = useState('idea_to_prd_pilot')
  const [goal, setGoal] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const selected = useMemo(
    () => runs.find(run => run.demo_run_id === selectedId) || runs[0] || null,
    [runs, selectedId],
  )
  const activeOffer = offers.find(offer => offer.offer_id === offerId)

  async function refresh(preferredId = selectedId) {
    const [offerResponse, runResponse] = await Promise.all([
      listDemoOffers(),
      listDemoRuns(),
    ])
    setOffers(offerResponse.offers)
    setRuns(runResponse.runs)
    if (preferredId) {
      setSelectedId(preferredId)
    } else if (runResponse.runs[0]) {
      setSelectedId(runResponse.runs[0].demo_run_id)
    }
    if (!goal && offerResponse.offers[0]) {
      const defaultOffer = offerResponse.offers.find(
        offer => offer.offer_id === offerId,
      ) || offerResponse.offers[0]
      setGoal(defaultOffer.default_goal)
    }
  }

  useEffect(() => {
    refresh().catch(exc => setError(String(exc)))
  }, [])

  useEffect(() => {
    if (activeOffer) setGoal(activeOffer.default_goal)
  }, [offerId])

  async function runAction(label: string, action: () => Promise<DemoRun>) {
    setBusy(label)
    setError('')
    try {
      const value = await action()
      await refresh(value.demo_run_id)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy('')
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    await runAction('create', () => createDemoRun({
      offer_id: offerId,
      founder_goal: goal,
    }))
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-300">
              Founder Control Center Multi-Product-Line Workbench v1
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white">
              Pilot-only / Demo Replay / Non-production / Not Operational Authority
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-zinc-300">
              Manage 2-3 deterministic offer streams as parallel-looking AI work.
              This page does not call Codex, Claude, OpenClaw, local_script, or
              operational DB. Every run is pilot_non_authoritative.
            </p>
          </div>
          <Link href="/vs001" className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300">
            Back to VS-001
          </Link>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[360px_1fr_420px]">
        <section className="space-y-4">
          <form onSubmit={submit} className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-5">
            <h2 className="font-medium text-white">Create demo stream</h2>
            <label className="mt-4 block text-xs text-zinc-400">
              Offer
              <select
                value={offerId}
                onChange={event => setOfferId(event.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white"
              >
                {offers.map(offer => (
                  <option key={offer.offer_id} value={offer.offer_id}>
                    {offer.display_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="mt-3 block text-xs text-zinc-400">
              Founder goal
              <textarea
                value={goal}
                onChange={event => setGoal(event.target.value)}
                rows={5}
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
              />
            </label>
            <button
              disabled={Boolean(busy)}
              className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
            >
              Create run
            </button>
          </form>

          <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium text-white">Offer streams</h2>
              <button onClick={() => refresh()} className="text-xs text-blue-400">
                Refresh
              </button>
            </div>
            <div className="space-y-2">
              {runs.map(run => (
                <button
                  key={run.demo_run_id}
                  onClick={() => setSelectedId(run.demo_run_id)}
                  className={`w-full rounded-lg border p-3 text-left hover:border-zinc-500 ${
                    selected?.demo_run_id === run.demo_run_id
                      ? 'border-blue-500/60 bg-blue-500/10'
                      : 'border-zinc-800 bg-zinc-950/60'
                  }`}
                >
                  <div className="text-sm text-white">{run.offer.display_name}</div>
                  <div className="mt-1 truncate text-xs text-zinc-500">
                    {run.founder_goal}
                  </div>
                  <div className={`mt-2 inline-flex rounded-full border px-2 py-0.5 text-[11px] ${statusTone[run.status] || statusTone.planned}`}>
                    {run.status}
                  </div>
                </button>
              ))}
              {!runs.length && <p className="text-sm text-zinc-500">No demo streams yet.</p>}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-5">
          {!selected ? (
            <div className="flex min-h-96 items-center justify-center text-zinc-500">
              Create a demo stream.
            </div>
          ) : (
            <div className="space-y-5">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
                  {selected.offer.offer_id}
                </p>
                <h2 className="mt-1 text-xl font-semibold text-white">
                  {selected.offer.display_name}
                </h2>
                <p className="mt-2 text-sm text-zinc-300">{selected.founder_goal}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <Badge label={selected.status} />
                  <Badge label={selected.authority} />
                  <Badge label={selected.mode} />
                </div>
              </div>

              <div className="grid gap-3">
                {selected.tasks.map((task, index) => (
                  <div key={task.task_id} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs text-zinc-500">Task {index + 1} · {task.executor_slot}</p>
                        <h3 className="mt-1 font-medium text-white">{task.title}</h3>
                      </div>
                      <span className={`rounded-full px-2 py-1 text-xs ${taskTone[task.status]}`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-zinc-400">{task.expected_output}</p>
                    <p className="mt-2 text-xs text-zinc-500">{task.audit_summary}</p>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-3 border-t border-zinc-800 pt-5">
                <button
                  onClick={() => runAction('advance', () => advanceDemoRun(selected.demo_run_id))}
                  disabled={Boolean(busy) || selected.status === 'go' || selected.status === 'no_go'}
                  className="rounded-lg border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm text-blue-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600"
                >
                  Advance next step
                </button>
                <button
                  onClick={() => runAction('go', () => decideDemoRun(selected.demo_run_id, 'go'))}
                  disabled={Boolean(busy) || selected.status !== 'ready_for_decision'}
                  className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600"
                >
                  Founder Go
                </button>
                <button
                  onClick={() => runAction('no_go', () => decideDemoRun(selected.demo_run_id, 'no_go'))}
                  disabled={Boolean(busy) || selected.status !== 'ready_for_decision'}
                  className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600"
                >
                  Founder No-Go
                </button>
              </div>

              {selected.final_asset && (
                <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
                  <h3 className="text-sm font-medium text-emerald-300">
                    {selected.final_asset.title}
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500">
                    {selected.final_asset.asset_id} · restricted · not public-safe
                  </p>
                  <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-300">
                    {selected.final_asset.content_markdown}
                  </pre>
                </div>
              )}
            </div>
          )}
        </section>

        <aside className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-5">
          <h2 className="font-medium text-white">Replay timeline</h2>
          <p className="mt-1 text-xs text-zinc-500">
            Audit-style demo events for recording public build material.
          </p>
          <div className="mt-5 space-y-3">
            {selected?.replay.map(event => (
              <div key={event.event_id} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-blue-300">{event.event_type}</span>
                  <span className="text-zinc-600">{event.actor}</span>
                </div>
                <h3 className="mt-1 text-sm font-medium text-white">{event.title}</h3>
                <p className="mt-1 text-xs text-zinc-400">{event.summary}</p>
              </div>
            ))}
            {!selected && <p className="text-sm text-zinc-500">No replay selected.</p>}
          </div>
        </aside>
      </div>
    </div>
  )
}

function Badge({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-300">
      {label}
    </span>
  )
}
