// ── v0.9 Code-Capable Runtime Bridge ──

export type CodeChangeStatus =
  | 'draft'
  | 'plan_generated'
  | 'plan_approved'
  | 'patch_generated'
  | 'checks_passed'
  | 'checks_warning'
  | 'checks_failed'
  | 'applied'
  | 'rolled_back'
  | 'rejected'

export interface CodeChangeRequest {
  id: number
  source_type: string
  source_id: string | null
  execution_request_id: number | null
  runtime_id: string | null
  title: string
  problem_summary: string | null
  plan_summary: string | null
  impact_scope: string | null
  risk_level: string
  files_expected: string[]
  files_changed: string[]
  patch_diff: string | null
  diff_summary: string | null
  check_result: Record<string, CheckItem> | null
  protected_file_check: ProtectedFileCheck | null
  applied_with_warning: boolean
  status: CodeChangeStatus
  plan_approved_by: string | null
  plan_approved_at: string | null
  applied_by: string | null
  applied_at: string | null
  rolled_back_by: string | null
  rolled_back_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CheckItem {
  name: string
  blocking: boolean
  passed: boolean
  output: string
}

export interface ProtectedFileCheck {
  pre_check: { passed: boolean; files: string[] }
  post_check: { passed: boolean; files: string[] }
}

export const STATUS_LABELS: Record<CodeChangeStatus, string> = {
  draft: '草稿',
  plan_generated: '方案已生成',
  plan_approved: '方案已批准',
  patch_generated: '补丁已生成',
  checks_passed: '检查通过',
  checks_warning: '检查告警',
  checks_failed: '检查未通过',
  applied: '已应用',
  rolled_back: '已回滚',
  rejected: '已拒绝',
}

export const STATUS_COLORS: Record<CodeChangeStatus, string> = {
  draft: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  plan_generated: 'bg-blue-400/10 text-blue-400 border-blue-400/30',
  plan_approved: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  patch_generated: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
  checks_passed: 'bg-green-500/10 text-green-400 border-green-500/30',
  checks_warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  checks_failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  applied: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  rolled_back: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  rejected: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
}

export const STATUS_ORDER: CodeChangeStatus[] = [
  'draft',
  'plan_generated',
  'plan_approved',
  'patch_generated',
  'checks_passed',
  'checks_warning',
  'checks_failed',
  'applied',
  'rolled_back',
  'rejected',
]

export const RISK_COLORS: Record<string, string> = {
  high: 'text-red-400',
  medium: 'text-yellow-400',
  low: 'text-green-400',
}
