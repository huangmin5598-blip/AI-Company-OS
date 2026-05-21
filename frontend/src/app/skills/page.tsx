'use client'

import { useEffect, useState } from 'react'
import { getSkillsMap } from '@/lib/api'

const COVERAGE_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  full:    { label: '充足', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
  partial: { label: '单点', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  gap:     { label: '缺口', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
}

const AGENT_COLORS = [
  'bg-blue-500/20 text-blue-300 border-blue-500/30',
  'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'bg-green-500/20 text-green-300 border-green-500/30',
  'bg-orange-500/20 text-orange-300 border-orange-500/30',
  'bg-pink-500/20 text-pink-300 border-pink-500/30',
  'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  'bg-teal-500/20 text-teal-300 border-teal-500/30',
  'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
]

export default function SkillsPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSkillsMap()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-sm text-[var(--muted)] animate-pulse">加载中...</div>
  }

  if (!data) {
    return <div className="text-sm text-red-400">加载失败</div>
  }

  // Agent color mapping
  const agentColorMap: Record<string, string> = {}
  let colorIdx = 0
  if (data.agent_skills) {
    Object.keys(data.agent_skills).forEach(a => {
      if (!agentColorMap[a]) {
        agentColorMap[a] = AGENT_COLORS[colorIdx % AGENT_COLORS.length]
        colorIdx++
      }
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">🛠️ 技能地图</h1>

      {/* ── Summary Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white">{data.total_skills}</div>
          <div className="text-xs text-[var(--muted)] mt-1">技能总数</div>
        </div>
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{data.total_agents_with_skills}</div>
          <div className="text-xs text-[var(--muted)] mt-1">已配技能 Agent</div>
        </div>
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {data.skills?.filter((s: any) => s.coverage === 'partial').length || 0}
          </div>
          <div className="text-xs text-[var(--muted)] mt-1">单点技能</div>
        </div>
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{data.task_gaps?.length || 0}</div>
          <div className="text-xs text-[var(--muted)] mt-1">任务技能缺口</div>
        </div>
      </div>

      {/* ── Skills Grid ── */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
        <h2 className="text-sm font-medium text-white mb-4">
          技能覆盖矩阵
          <span className="ml-2 text-xs text-[var(--muted)]">🟢 充足 (≥2 Agent) · 🟡 单点 (1 Agent) · 🔴 缺口 (0 Agent)</span>
        </h2>

        {data.skills?.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {data.skills.map((skill: any) => {
              const cfg = COVERAGE_CONFIG[skill.coverage] || COVERAGE_CONFIG.gap
              const dot = skill.coverage === 'full' ? '🟢' : skill.coverage === 'partial' ? '🟡' : '🔴'
              return (
                <div key={skill.skill} className={`${cfg.bg} border ${cfg.border} rounded-lg p-3`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">{skill.skill}</span>
                    <span className={`text-xs ${cfg.color}`}>{dot} {cfg.label}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {skill.agents.map((agent: string) => (
                      <span
                        key={agent}
                        className={`text-[10px] px-1.5 py-0.5 rounded border ${
                          agentColorMap[agent] || 'bg-zinc-700/50 text-zinc-300 border-zinc-600'
                        }`}
                      >
                        {agent}
                      </span>
                    ))}
                    {skill.agents.length === 0 && (
                      <span className="text-[10px] text-red-400/70">无 Agent 具备此技能</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-sm text-[var(--muted)] text-center py-8">
            还没有 Agent 配置技能。请在 <a href="/agents" className="text-blue-400 hover:text-blue-300">Agent 页面</a> 或通过 API 为 Agent 配置技能标签。
          </div>
        )}
      </div>

      {/* ── Task Gaps ── */}
      {data.task_gaps?.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-6">
          <h2 className="text-sm font-medium text-red-400 mb-3">⚠️ 任务技能缺口</h2>
          <p className="text-xs text-[var(--muted)] mb-3">
            以下任务要求了当前没有任何 Agent 具备的技能：
          </p>
          <div className="space-y-2">
            {data.task_gaps.map((gap: any, i: number) => (
              <div key={i} className="flex items-center gap-3 text-sm bg-red-500/5 rounded px-3 py-2">
                <span className="px-1.5 py-0.5 bg-red-500/20 rounded text-xs text-red-400 font-mono">
                  {gap.skill}
                </span>
                <a
                  href={`/tasks/${gap.task_id}`}
                  className="text-gray-300 hover:text-white transition-colors truncate"
                >
                  #{gap.task_id} {gap.task_title}
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Agent Skills Overview ── */}
      {data.agent_skills && Object.keys(data.agent_skills).length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-lg p-6">
          <h2 className="text-sm font-medium text-white mb-3">🤖 Agent 技能明细</h2>
          <div className="space-y-3">
            {Object.entries(data.agent_skills as Record<string, string[]>).map(([agent, skills]) => (
              <div key={agent} className="flex items-start gap-3">
                <span className={`text-xs font-medium px-2 py-1 rounded border shrink-0 mt-0.5 ${
                  agentColorMap[agent] || 'bg-zinc-700 text-zinc-300 border-zinc-600'
                }`}>
                  {agent}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {skills.map((s: string) => (
                    <span key={s} className="text-xs px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded text-blue-400">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
