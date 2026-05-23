'use client'

import { useEffect, useState, useCallback } from 'react'
import { searchMemory, getKnowledgeProposals, decideProposal } from '@/lib/api'
import type { MemorySearchResult, KnowledgeProposal } from '@/types/api'

const MEMORY_TYPE_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  failure_pattern: { label: '失败模式', icon: '🔴', color: 'text-red-400' },
  decision_pattern: { label: '决策模式', icon: '🟡', color: 'text-yellow-400' },
  tool_gap: { label: '工具缺口', icon: '🔧', color: 'text-blue-400' },
  context_update: { label: '上下文更新', icon: '💡', color: 'text-green-400' },
  sop_hint: { label: 'SOP', icon: '📋', color: 'text-purple-400' },
}

const BUSINESS_LINES = ['', 'amazon', 'finance', 'novel', 'general']
const MEMORY_TYPES = ['', 'failure_pattern', 'decision_pattern', 'tool_gap', 'context_update', 'sop_hint']

export default function MemoryPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<MemorySearchResult[]>([])
  const [proposals, setProposals] = useState<KnowledgeProposal[]>([])
  const [businessLine, setBusinessLine] = useState('')
  const [memoryType, setMemoryType] = useState('')
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState<number | null>(null)
  const [notes, setNotes] = useState('')
  const [message, setMessage] = useState('')

  const loadProposals = useCallback(async () => {
    try {
      const data = await getKnowledgeProposals('draft')
      setProposals(data)
    } catch { /* ignore */ }
  }, [])

  const loadSearch = useCallback(async () => {
    try {
      const data = await searchMemory(query, businessLine || undefined, memoryType || undefined)
      setResults(data)
    } catch { /* ignore */ }
  }, [query, businessLine, memoryType])

  useEffect(() => {
    Promise.all([loadSearch(), loadProposals()]).finally(() => setLoading(false))
  }, [loadSearch, loadProposals])

  useEffect(() => {
    if (!loading) loadSearch()
  }, [query, businessLine, memoryType, loadSearch])

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    await loadSearch()
    setLoading(false)
  }

  async function handleDecide(proposalId: number, decision: string) {
    try {
      const payload: { status: string; founder_notes?: string } = { status: decision }
      if (notes) payload.founder_notes = notes
      await decideProposal(proposalId, payload)
      setConfirming(null)
      setNotes('')
      setMessage(decision === 'approved' ? '✅ 已确认并写入组织记忆' : decision === 'revised' ? '✏️ 已标记为修订' : '❌ 已拒绝')
      await loadProposals()
      await loadSearch()
      setTimeout(() => setMessage(''), 3000)
    } catch (e: any) {
      setMessage(`❌ 操作失败: ${e.message}`)
    }
  }

  function buildSourceChain(m: MemorySearchResult): string {
    const parts: string[] = []
    if (m.source_candidate_id) parts.push(`📄 learning_candidate #${m.source_candidate_id}`)
    if (m.source_review_id) parts.push(`📝 review #${m.source_review_id}`)
    if (m.source_task_id) parts.push(`📋 task #${m.source_task_id}`)
    if (m.source_goal_session_id) parts.push(`🎯 goal_session #${m.source_goal_session_id}`)
    return parts.length ? parts.join(' → ') : '—'
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold">🧠 Company Memory 组织记忆</h1>
        <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-800">v0.4</span>
      </div>

      {message && (
        <div className="bg-zinc-800 border border-zinc-600 rounded px-4 py-2 mb-4 text-sm">{message}</div>
      )}

      {!loading && proposals.length > 0 && (
        <div className="bg-yellow-900/10 border border-yellow-600/30 rounded-lg p-4 mb-6">
          <h2 className="text-sm font-medium text-yellow-400 mb-3">
            📋 待处理 Knowledge Proposals ({proposals.length})
          </h2>
          <div className="space-y-3">
            {proposals.map((p) => (
              <div key={p.id} className="bg-zinc-800 rounded p-3 border border-zinc-700">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${MEMORY_TYPE_LABELS[p.proposal_type]?.color || 'text-gray-400'} bg-zinc-700`}>
                      {MEMORY_TYPE_LABELS[p.proposal_type]?.icon || '📌'} {MEMORY_TYPE_LABELS[p.proposal_type]?.label || p.proposal_type}
                    </span>
                    <h3 className="text-sm font-medium mt-1">{p.title}</h3>
                    {p.summary && <p className="text-xs text-zinc-400 mt-0.5 line-clamp-2">{p.summary}</p>}
                    <p className="text-xs text-zinc-500 mt-1">来源: Learning Candidate #{p.source_candidate_id}</p>
                  </div>
                </div>

                {confirming === p.id ? (
                  <div className="mt-2 space-y-2">
                    <textarea
                      className="w-full bg-zinc-700 rounded px-2 py-1 text-xs"
                      rows={2}
                      placeholder="备注（可选）"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <button onClick={() => handleDecide(p.id, 'approved')} className="text-xs px-3 py-1 rounded bg-green-700 hover:bg-green-600 text-white">✅ 确认</button>
                      <button onClick={() => handleDecide(p.id, 'revised')} className="text-xs px-3 py-1 rounded bg-yellow-700 hover:bg-yellow-600 text-white">✏️ 修改</button>
                      <button onClick={() => handleDecide(p.id, 'rejected')} className="text-xs px-3 py-1 rounded bg-red-700 hover:bg-red-600 text-white">❌ 拒绝</button>
                      <button onClick={() => { setConfirming(null); setNotes('') }} className="text-xs px-3 py-1 rounded bg-zinc-600 hover:bg-zinc-500 text-white">取消</button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirming(p.id)}
                    className="mt-2 text-xs px-3 py-1 rounded bg-zinc-700 hover:bg-zinc-600 text-zinc-300"
                  >
                    处理提案
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="text"
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm"
          placeholder="搜索组织记忆... (FTS5全文搜索)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="bg-zinc-800 border border-zinc-700 rounded px-2 py-2 text-sm"
          value={businessLine}
          onChange={(e) => setBusinessLine(e.target.value)}
        >
          <option value="">所有业务线</option>
          {BUSINESS_LINES.filter(Boolean).map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
        <select
          className="bg-zinc-800 border border-zinc-700 rounded px-2 py-2 text-sm"
          value={memoryType}
          onChange={(e) => setMemoryType(e.target.value)}
        >
          <option value="">所有类型</option>
          {MEMORY_TYPES.filter(Boolean).map((t) => (
            <option key={t} value={t}>{MEMORY_TYPE_LABELS[t]?.label || t}</option>
          ))}
        </select>
        <button type="submit" className="px-4 py-2 rounded bg-blue-700 hover:bg-blue-600 text-sm text-white">
          搜索
        </button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="text-center py-12 text-zinc-500">加载中...</div>
      ) : results.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          {query || businessLine || memoryType
            ? '没有找到匹配的记忆。换个关键词试试？'
            : '暂无组织记忆。Learning Candidate 批准后会自动生成 Knowledge Proposal。'}
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-zinc-500">共 {results.length} 条结果</p>
          {results.map((m) => (
            <div key={m.id} className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4 hover:border-zinc-600 transition-colors">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${MEMORY_TYPE_LABELS[m.memory_type]?.color || 'text-gray-400'} bg-zinc-700`}>
                  {MEMORY_TYPE_LABELS[m.memory_type]?.icon || '📌'} {MEMORY_TYPE_LABELS[m.memory_type]?.label || m.memory_type}
                </span>
                {m.business_line && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-800">{m.business_line}</span>
                )}
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  m.status === 'active' ? 'bg-green-900/30 text-green-300 border border-green-800' : 'bg-zinc-700 text-zinc-400'
                }`}>
                  {m.status}
                </span>
                {m.version > 1 && (
                  <span className="text-xs text-zinc-500">v{m.version}</span>
                )}
              </div>
              <h3 className="text-sm font-medium text-white">{m.title}</h3>
              {m.snippet && (
                <p className="text-xs text-zinc-300 mt-1" dangerouslySetInnerHTML={{ __html: m.snippet }} />
              )}
              {m.summary && !m.snippet && (
                <p className="text-xs text-zinc-400 mt-1">{m.summary}</p>
              )}
              <p className="text-xs text-zinc-600 mt-2">
                📎 来源链: {buildSourceChain(m)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
