'use client'

import { useEffect, useState } from 'react'
import { getCeoActionLogs } from '@/lib/api'
import type { CeoActionLog } from '@/types/api'

const INTENT_OPTIONS = ['all', 'goal_intake', 'approval_action'] as const
const RESULT_OPTIONS = ['all', 'success', 'failed', 'ambiguous'] as const

export default function ActionLogsPage() {
  const [logs, setLogs] = useState<CeoActionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [intentFilter, setIntentFilter] = useState<string>('all')
  const [resultFilter, setResultFilter] = useState<string>('all')

  useEffect(() => {
    loadLogs()
  }, [intentFilter, resultFilter])

  async function loadLogs() {
    setLoading(true)
    try {
      const params: { intent_type?: string; result_status?: string } = {}
      if (intentFilter !== 'all') params.intent_type = intentFilter
      if (resultFilter !== 'all') params.result_status = resultFilter
      const data = await getCeoActionLogs(params)
      setLogs(data.sort((a, b) => {
        const aDate = a.created_at ? new Date(a.created_at).getTime() : 0
        const bDate = b.created_at ? new Date(b.created_at).getTime() : 0
        return bDate - aDate
      }))
    } catch (e) {
      console.error('Failed to load action logs', e)
    } finally {
      setLoading(false)
    }
  }

  function resultColor(status: string): string {
    switch (status) {
      case 'success': return 'bg-green-500/20 text-green-300 border-green-500/40'
      case 'failed': return 'bg-red-500/20 text-red-300 border-red-500/40'
      case 'ambiguous': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      case 'cancelled': return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/40'
    }
  }

  function intentIcon(intent: string): string {
    switch (intent) {
      case 'goal_intake': return '🎯'
      case 'approval_action': return '✅'
      default: return '📋'
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">📋 CEO Action Logs 操作日志</h1>
        <p className="text-sm text-[var(--muted)] mt-1">CEO 智能体所有操作的历史记录</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--muted)]">意图类型:</span>
          <div className="flex gap-1">
            {INTENT_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => setIntentFilter(opt)}
                className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
                  intentFilter === opt
                    ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                    : 'bg-[var(--background)] text-[var(--muted)] border-[var(--card-border)] hover:text-white'
                }`}
              >
                {opt === 'all' ? '全部' : opt}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--muted)]">结果状态:</span>
          <div className="flex gap-1">
            {RESULT_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => setResultFilter(opt)}
                className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
                  resultFilter === opt
                    ? 'bg-[var(--accent)] text-white border-[var(--accent)]'
                    : 'bg-[var(--background)] text-[var(--muted)] border-[var(--card-border)] hover:text-white'
                }`}
              >
                {opt === 'all' ? '全部' : opt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Logs */}
      {loading ? (
        <div className="text-[var(--muted)] text-center py-16">加载中...</div>
      ) : logs.length === 0 ? (
        <div className="text-[var(--muted)] text-center py-16 bg-[var(--card)] border border-[var(--card-border)] rounded-xl">
          暂无操作日志
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {logs.map((log) => (
            <div
              key={log.id}
              className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-4 hover:border-zinc-600 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{intentIcon(log.intent_type)}</span>
                  <span className="text-xs text-[var(--muted)] font-medium">{log.intent_type}</span>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded border ${resultColor(log.result_status)}`}>
                  {log.result_status}
                </span>
              </div>
              <p className="text-sm text-white mb-2 line-clamp-3">{log.raw_user_message}</p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                {log.target_type && log.target_id !== null && (
                  <span className="text-[10px] text-[var(--muted)]">
                    目标: {log.target_type} #{log.target_id}
                  </span>
                )}
                {log.confidence !== null && (
                  <span className="text-[10px] text-[var(--muted)]">
                    置信度: {(log.confidence * 100).toFixed(0)}%
                  </span>
                )}
                <span className="text-[10px] text-[var(--muted)]">{formatDate(log.created_at)}</span>
              </div>
              {log.result_summary && (
                <p className="text-[10px] text-[var(--muted)] mt-2 italic line-clamp-2">{log.result_summary}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
