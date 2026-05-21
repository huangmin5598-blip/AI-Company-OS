'use client'

import { useEffect, useState } from 'react'
import { getFailureAnalysis, getGapAnalysis } from '@/lib/api'

export default function AnalysisPage() {
  const [failures, setFailures] = useState<any>(null)
  const [gaps, setGaps] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'failures' | 'gaps'>('failures')

  useEffect(() => {
    Promise.all([getFailureAnalysis(), getGapAnalysis()])
      .then(([f, g]) => { setFailures(f); setGaps(g) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">📊 系统分析</h1>

      {/* Tab bar */}
      <div className="flex gap-1 bg-zinc-800/50 rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab('failures')}
          className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
            tab === 'failures' ? 'bg-zinc-700 text-white' : 'text-[var(--muted)] hover:text-white'
          }`}
        >
          ❌ 失败分析
        </button>
        <button
          onClick={() => setTab('gaps')}
          className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
            tab === 'gaps' ? 'bg-zinc-700 text-white' : 'text-[var(--muted)] hover:text-white'
          }`}
        >
          ⚠️ 技能缺口
        </button>
      </div>

      {tab === 'failures' && failures && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-400">{failures.total_failed}</div>
              <div className="text-xs text-[var(--muted)] mt-1">失败任务</div>
            </div>
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">{failures.total_tasks}</div>
              <div className="text-xs text-[var(--muted)] mt-1">总任务数</div>
            </div>
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className={`text-2xl font-bold ${failures.failure_rate > 30 ? 'text-red-400' : failures.failure_rate > 10 ? 'text-yellow-400' : 'text-green-400'}`}>
                {failures.failure_rate}%
              </div>
              <div className="text-xs text-[var(--muted)] mt-1">失败率</div>
            </div>
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-white">{failures.recommendations?.length || 0}</div>
              <div className="text-xs text-[var(--muted)] mt-1">改进建议</div>
            </div>
          </div>

          {/* Recommendations */}
          {failures.recommendations?.length > 0 && (
            <div className="bg-orange-500/5 border border-orange-500/20 rounded-lg p-6">
              <h2 className="text-sm font-medium text-orange-400 mb-3">💡 改进建议</h2>
              <div className="space-y-2">
                {failures.recommendations.map((r: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 text-sm bg-orange-500/5 rounded p-3">
                    <span className="text-orange-400 mt-0.5">💡</span>
                    <div>
                      <p className="text-gray-200">{r.suggestion}</p>
                      <div className="flex gap-2 mt-1 text-xs text-[var(--muted)]">
                        {r.count && <span>出现 {r.count} 次</span>}
                        {r.agent && <span>Agent: {r.agent}</span>}
                        {r.fail_rate && <span>失败率: {r.fail_rate}%</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* By Reason */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
              <h2 className="text-sm font-medium text-white mb-3">📊 失败原因分布</h2>
              {failures.by_reason?.length > 0 ? (
                <div className="space-y-2">
                  {failures.by_reason.map((r: any) => {
                    const maxCount = Math.max(...failures.by_reason.map((x: any) => x.count))
                    const pct = (r.count / maxCount) * 100
                    return (
                      <div key={r.reason} className="flex items-center gap-2">
                        <span className="text-xs text-[var(--muted)] w-24 truncate text-right" title={r.reason}>
                          {r.reason}
                        </span>
                        <div className="flex-1 h-5 bg-zinc-800 rounded overflow-hidden">
                          <div
                            className="h-full bg-red-500/60 rounded"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-white w-6 text-right">{r.count}</span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-xs text-[var(--muted)]">暂无失败原因数据</div>
              )}
            </div>

            {/* By Agent */}
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
              <h2 className="text-sm font-medium text-white mb-3">🤖 Agent 失败分布</h2>
              {failures.by_agent?.length > 0 ? (
                <div className="space-y-2">
                  {failures.by_agent.map((r: any) => {
                    const maxCount = Math.max(...failures.by_agent.map((x: any) => x.count))
                    const pct = (r.count / maxCount) * 100
                    return (
                      <div key={r.agent} className="flex items-center gap-2">
                        <span className="text-xs text-[var(--muted)] w-24 truncate text-right">{r.agent}</span>
                        <div className="flex-1 h-5 bg-zinc-800 rounded overflow-hidden">
                          <div
                            className="h-full bg-orange-500/60 rounded"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-white w-6 text-right">{r.count}</span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-xs text-[var(--muted)]">无失败数据</div>
              )}
            </div>
          </div>

          {/* Recent Failures */}
          {failures.recent_failures?.length > 0 && (
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4">
              <h2 className="text-sm font-medium text-white mb-3">🕐 最近失败任务</h2>
              <div className="space-y-1">
                {failures.recent_failures.map((f: any) => (
                  <a
                    key={f.task_id}
                    href={`/tasks/${f.task_id}`}
                    className="flex items-center gap-3 text-sm px-3 py-2 rounded hover:bg-zinc-800/50 transition-colors"
                  >
                    <span className="text-red-400">#{f.task_id}</span>
                    <span className="text-gray-300 truncate flex-1">{f.title}</span>
                    <span className="text-xs text-[var(--muted)]">{f.agent_id}</span>
                    <span className="text-xs text-red-400/70">{f.failure_reason || '未知'}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'gaps' && gaps && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-400">{gaps.total_gap_skills}</div>
              <div className="text-xs text-[var(--muted)] mt-1">缺口技能数</div>
            </div>
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">
                {gaps.recommendations?.filter((r: any) => r.severity === 'high').length || 0}
              </div>
              <div className="text-xs text-[var(--muted)] mt-1">高优先级缺口</div>
            </div>
            <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {gaps.recommendations?.filter((r: any) => r.severity === 'medium').length || 0}
              </div>
              <div className="text-xs text-[var(--muted)] mt-1">中优先级缺口</div>
            </div>
          </div>

          {/* Recommendations */}
          {gaps.recommendations?.length > 0 ? (
            <div className="space-y-2">
              {gaps.recommendations.map((r: any, i: number) => (
                <div
                  key={i}
                  className={`rounded-lg p-4 border ${
                    r.severity === 'high'
                      ? 'bg-red-500/5 border-red-500/20'
                      : r.severity === 'medium'
                      ? 'bg-yellow-500/5 border-yellow-500/20'
                      : 'bg-zinc-800/50 border-zinc-700/30'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-medium ${
                      r.severity === 'high' ? 'text-red-400' : r.severity === 'medium' ? 'text-yellow-400' : 'text-[var(--muted)]'
                    }`}>
                      {r.severity === 'high' ? '🔴' : r.severity === 'medium' ? '🟡' : '🟢'} {r.skill}
                    </span>
                    <span className="text-xs text-[var(--muted)]">×{r.occurrence_count}</span>
                  </div>
                  <p className="text-sm text-gray-300">{r.suggestion}</p>
                  <a
                    href={`/skills`}
                    className="mt-2 inline-block text-xs text-blue-400 hover:text-blue-300"
                  >
                    查看技能地图 →
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-[var(--muted)] text-center py-8">🎉 暂无技能缺口</div>
          )}
        </>
      )}
    </div>
  )
}
