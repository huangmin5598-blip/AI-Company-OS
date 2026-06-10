'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

import { approvePilotAsset, getPilotAsset } from '@/lib/vs001Api'
import type { PilotAssetEnvelope } from '@/types/vs001'


export default function PilotAssetPage() {
  const params = useParams<{ asset_id: string }>()
  const [asset, setAsset] = useState<PilotAssetEnvelope | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function refresh() {
    setAsset(await getPilotAsset(params.asset_id, true))
  }

  useEffect(() => {
    refresh().catch(exc => setError(String(exc)))
  }, [params.asset_id])

  async function approve() {
    setBusy(true)
    setError('')
    try {
      setAsset(await approvePilotAsset(params.asset_id))
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-300">
          VS-002 Approved Output to Asset
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-white">
          Pilot / Non-production / Restricted / Not Public-safe
        </h1>
        <p className="mt-2 text-sm text-zinc-300">
          This record is pilot_non_authoritative. Approval does not publish it,
          promote Company Context, or update the Learning Loop.
        </p>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {!asset ? (
        <div className="text-zinc-500">Loading Pilot Asset...</div>
      ) : (
        <section className="space-y-5 rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-white">
                {asset.asset.title}
              </h2>
              <p className="mt-1 break-all text-xs text-zinc-500">
                {asset.asset.asset_id}
              </p>
            </div>
            <span className="rounded-full border border-blue-500/40 px-3 py-1 text-xs text-blue-300">
              {asset.asset.status}
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Info label="Authority" value={asset.asset.authority} />
            <Info label="Visibility" value={asset.asset.visibility} />
            <Info label="Public-safe" value="false" />
            <Info
              label="Approval"
              value={asset.approval?.decision || 'requested'}
            />
          </div>

          <div className="flex flex-wrap gap-3 border-y border-zinc-800 py-4">
            <button
              onClick={approve}
              disabled={busy || asset.asset.status !== 'candidate'}
              className="rounded-lg border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm text-blue-300 disabled:border-zinc-800 disabled:bg-zinc-900 disabled:text-zinc-600"
            >
              Approve Asset Candidate
            </button>
            <Link
              href="/vs001"
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300"
            >
              Back to WorkOrder
            </Link>
          </div>

          <div>
            <h3 className="text-sm font-medium text-zinc-300">
              Immutable Markdown Artifact
            </h3>
            <p className="mt-1 break-all text-xs text-zinc-500">
              {asset.content?.content_hash}
            </p>
            <pre className="mt-3 min-h-64 whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm text-zinc-300">
              {asset.content?.text || 'Content unavailable'}
            </pre>
          </div>
        </section>
      )}
    </div>
  )
}


function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 break-all text-sm text-zinc-200">{value}</div>
    </div>
  )
}
