'use client'

import { useEffect, useState } from 'react'
import { getRuns, getBusinessLines } from '@/lib/api'
import type { ExecutionRecord, BusinessLine } from '@/types/api'

export default function RunsPage() {
  const [runs, setRuns] = useState<ExecutionRecord[]>([])
  const [lines, setLines] = useState<BusinessLine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filterLine, setFilterLine] = useState('')
  const [filterResult, setFilterResult] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  async function loadRuns() {
    try {
      const params: Record<string, string | number> = { limit: 100 }
      if (filterLine) params.business_line = filterLine
      if (filterResult) params.result = filterResult
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const r = await getRuns(params as any)
      setRuns(r)
      setError(null)
    } catch {
      setError('无法连接后端')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    getBusinessLines().then(setLines).catch(() => {})
    loadRuns()
  }, [])

  useEffect(() => { loadRuns() }, [filterLine, filterResult, dateFrom, dateTo])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[var(--muted)]">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="text-red-400 text-lg">⚠️ {error}</div>
        <button onClick={loadRuns} className="px-4 py-2 bg-blue-600 rounded text-sm">重试</button>
      </div>
    )
  }

  const passedCount = runs.filter(r => r.result === 'passed').length
  const failedCount = runs.filter(r => r.result === 'failed').length
  const totalCost = runs.reduce((s, r) => s + (r.cost_usd || 0), 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium text-white">执行记录</h1>
        <div className="text-xs text-[var(--muted)]">
          ✅ {passedCount} 失败 ❌ {failedCount} 总计 💰 ${totalCost.toFixed(6)}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-[var(--muted)]">业务线</label>
          <select
            value={filterLine}
            onChange={e => setFilterLine(e.target.value)}
            className="bg-zinc-800 text-xs text-white rounded px-2 py-1.5 border border-zinc-700"
          >
            <option value="">全部</option>
            {lines.map(l => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-[var(--muted)]">结果</label>
          <select
            value={filterResult}
            onChange={e => setFilterResult(e.target.value)}
            className="bg-zinc-800 text-xs text-white rounded px-2 py-1.5 border border-zinc-700"
          >
            <option value="">全部</option>
            <option value="passed">通过 ✅</option>
            <option value="failed">失败 ❌</option>
            <option value="pending">进行中 ⏳</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-[var(--muted)]">从</label>
          <input
            type="date"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className="bg-zinc-800 text-xs text-white rounded px-2 py-1.5 border border-zinc-700"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-[var(--muted)]">到</label>
          <input
            type="date"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className="bg-zinc-800 text-xs text-white rounded px-2 py-1.5 border border-zinc-700"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--card-border)] text-[var(--muted)]">
                <th className="text-left p-3 font-medium">日期</th>
                <th className="text-left p-3 font-medium">业务线</th>
                <th className="text-left p-3 font-medium">任务</th>
                <th className="text-right p-3 font-medium">字数</th>
                <th className="text-center p-3 font-medium">结果</th>
                <th className="text-right p-3 font-medium">成本</th>
                <th className="text-left p-3 font-medium">详情</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.id} className="border-b border-[var(--card-border)] last:border-0 hover:bg-zinc-800/50 transition-colors">
                  <td className="p-3 text-white/80 whitespace-nowrap">{r.date}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs">{r.business_line}</span>
                  </td>
                  <td className="p-3 text-white/80 truncate max-w-[240px]" title={r.title || r.task_id || ''}>
                    {r.title || r.task_id || '-'}
                  </td>
                  <td className="p-3 text-right text-white/80 whitespace-nowrap">
                    {r.word_count > 0 ? r.word_count.toLocaleString() : '-'}
                  </td>
                  <td className="p-3 text-center">
                    {r.result === 'passed' ? (
                      <span className="text-green-400" title="通过">✅</span>
                    ) : r.result === 'failed' ? (
                      <span className="text-red-400 cursor-help" title={r.result_detail || '失败'}>❌</span>
                    ) : (
                      <span className="text-yellow-400">⏳</span>
                    )}
                  </td>
                  <td className="p-3 text-right text-white/80 whitespace-nowrap font-mono">
                    ${r.cost_usd.toFixed(6)}
                  </td>
                  <td className="p-3">
                    {r.result_detail && (
                      <span className="text-xs text-red-400/70" title={r.result_detail}>
                        {r.result_detail.length > 20 ? r.result_detail.slice(0, 20) + '...' : r.result_detail}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {runs.length === 0 && (
          <div className="text-center text-[var(--muted)] py-12">没有匹配的执行记录</div>
        )}
      </div>
    </div>
  )
}
