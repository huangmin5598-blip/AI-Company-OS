export type DemoOffer = {
  offer_id: 'idea_to_prd_pilot' | 'spoken_agent_offer' | 'clip_matrix_agent'
  display_name: string
  tagline: string
  default_goal: string
}

export type DemoTaskStatus = 'planned' | 'queued' | 'running' | 'waiting_review' | 'done'
export type DemoRunStatus = 'planned' | 'active' | 'ready_for_decision' | 'go' | 'no_go'

export type DemoTask = {
  task_id: string
  title: string
  executor_slot: string
  status: DemoTaskStatus
  expected_output: string
  audit_summary: string
}

export type DemoReplayEvent = {
  event_id: string
  event_type: string
  title: string
  summary: string
  actor: string
  created_at: string
}

export type DemoAsset = {
  asset_id: string
  title: string
  content_markdown: string
  authority: 'pilot_non_authoritative'
  visibility: 'restricted'
  public_safe: false
}

export type DemoRun = {
  demo_run_id: string
  offer: {
    offer_id: DemoOffer['offer_id']
    display_name: string
    tagline: string
  }
  founder_goal: string
  status: DemoRunStatus
  authority: 'pilot_non_authoritative'
  mode: 'demo_spine_pilot'
  source_path: 'founder_control_center_demo_spine'
  created_at: string
  updated_at: string
  tasks: DemoTask[]
  replay: DemoReplayEvent[]
  final_asset: DemoAsset | null
  founder_decision: 'go' | 'no_go' | null
  governance: {
    authority: 'pilot_non_authoritative'
    mode: 'demo_spine_pilot'
    pilot_only: true
    operational_authority: false
    real_runtime_invoked: false
    public_safe: false
  }
}
