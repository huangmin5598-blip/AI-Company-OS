// ── v0.8 Controlled Execution Bridge ──

export interface ExecutionRequest {
  id: number
  source_type: string
  source_id: string | null
  proposal_id: number | null
  task_id: number | null
  runtime_id: string | null
  action_type: string
  action_payload: Record<string, unknown>
  risk_level: string
  dry_run_required: boolean
  dry_run_result: Record<string, unknown> | null
  status: ExecutionRequestStatus
  execute_confirmed_by: string | null
  execute_confirmed_at: string | null
  execute_confirmation_note: string | null
  executed_at: string | null
  execution_result: Record<string, unknown> | null
  verification_result: Record<string, unknown> | null
  verified_by: string | null
  verified_at: string | null
  created_at: string | null
  updated_at: string | null
}

export type ExecutionRequestStatus =
  | 'draft'
  | 'pending_confirmation'
  | 'dry_run_completed'
  | 'approved_for_execute'
  | 'executed'
  | 'verification_pending'
  | 'verified_success'
  | 'verified_failed'
  | 'cancelled'

export const STATUS_LABELS: Record<ExecutionRequestStatus, string> = {
  draft: '草稿',
  pending_confirmation: '待确认',
  dry_run_completed: 'Dry-Run 完成',
  approved_for_execute: '已批准执行',
  executed: '已执行',
  verification_pending: '待验证',
  verified_success: '验证成功',
  verified_failed: '验证失败',
  cancelled: '已取消',
}

export const STATUS_COLORS: Record<ExecutionRequestStatus, string> = {
  draft: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  pending_confirmation: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  dry_run_completed: 'bg-blue-400/10 text-blue-400 border-blue-400/30',
  approved_for_execute: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  executed: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  verification_pending: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  verified_success: 'bg-green-500/10 text-green-400 border-green-500/30',
  verified_failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  cancelled: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
}

export const ACTION_TYPE_LABELS: Record<string, string> = {
  diagnose_task: '🔍 诊断任务',
  create_retry_task: '🔄 创建重试任务',
  generate_memory_update_draft: '🧠 知识更新草稿',
  run_status_check: '📊 状态检查',
  run_dry_run_command: '⚡ Dry-Run 命令',
}

export const ACTION_TYPE_COLORS: Record<string, string> = {
  diagnose_task: 'bg-blue-500/10 text-blue-400',
  create_retry_task: 'bg-orange-500/10 text-orange-400',
  generate_memory_update_draft: 'bg-emerald-500/10 text-emerald-400',
  run_status_check: 'bg-cyan-500/10 text-cyan-400',
  run_dry_run_command: 'bg-purple-500/10 text-purple-400',
}

/** Allowed transitions for status steps in the UI */
export const STATUS_STEPS: {
  from: ExecutionRequestStatus[]
  to: ExecutionRequestStatus
  label: string
  action: string
}[] = [
  { from: ['pending_confirmation'], to: 'dry_run_completed', label: '1. Dry-Run', action: 'dry-run' },
  { from: ['pending_confirmation', 'dry_run_completed'], to: 'approved_for_execute', label: '2. 确认执行', action: 'confirm' },
  { from: ['approved_for_execute'], to: 'executed', label: '3. 执行', action: 'execute' },
  { from: ['executed'], to: 'verified_success', label: '4. 验证', action: 'verify' },
]
