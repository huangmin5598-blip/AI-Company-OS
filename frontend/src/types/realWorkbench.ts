export type RealWorkbenchProductLineId =
  | 'idea_to_prd_pilot'
  | 'spoken_agent_offer'
  | 'clip_matrix_agent'

export type RealWorkbenchExecutorSlot =
  | 'codex_slot'
  | 'claude_slot'
  | 'hermes_slot'
  | 'openclaw_slot'
  | 'local_script_slot'
  | 'manual_founder_slot'

export type RealWorkbenchTemplate = {
  product_line_id: RealWorkbenchProductLineId
  display_name: string
  tagline: string
  default_goal: string
  task_count: number
  authority: 'pilot_non_authoritative'
  mode: 'real_workbench_pilot'
}

export type RealWorkbenchTask = {
  task_id: string
  step_index: number
  title: string
  executor_slot: string
  status: 'planned'
  expected_output: string
  audit_summary: string
  authority: 'pilot_non_authoritative'
  created_at: string
  assigned_slot: RealWorkbenchExecutorSlot | null
  assignment_status: 'unassigned' | 'assigned' | 'revised'
  assignment_note: string
  assigned_by: string | null
  assigned_at: string | null
  updated_at: string
}

export type RealWorkbenchRun = {
  run_id: string
  product_line: {
    product_line_id: RealWorkbenchProductLineId
    display_name: string
    tagline: string
  }
  founder_goal: string
  status: 'planned' | 'active' | 'ready_for_decision' | 'go' | 'no_go'
  authority: 'pilot_non_authoritative'
  mode: 'real_workbench_pilot'
  source_path: 'founder_control_center_real_workbench'
  task_plan_hash: string
  created_at: string
  updated_at: string
  task_plan: RealWorkbenchTask[]
  governance: {
    authority: 'pilot_non_authoritative'
    mode: 'real_workbench_pilot'
    pilot_only: true
    operational_authority: false
    real_runtime_invoked: false
    scheduler_invoked: false
    worker_pool_invoked: false
    manual_dispatch_only: true
    public_safe: false
  }
}
