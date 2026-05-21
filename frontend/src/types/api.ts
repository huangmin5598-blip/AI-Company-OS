export interface Agent {
  id: string
  name: string
  identity: string | null
  workspace: string | null
  model: string | null
  routing_rules: number
  agent_type: string
  role: string | null
  skills: string | null
  status: string
  total_cost_usd: number
  last_active_at: string | null
  total_runs: number
  recent_task: string | null
  discovery_status: string
  activity_status: string
  health_status: string
}

export interface BusinessLine {
  id: string
  name: string
  status: string
  total_runs: number
  failed_runs: number
  total_cost_usd: number
  last_run_date: string | null
  last_run_result: string | null
  recent_artifacts: string[]
}

export interface ExecutionRecord {
  id: string
  date: string
  business_line: string
  task_id: string | null
  title: string | null
  word_count: number
  result: string | null
  result_detail: string | null
  cost_usd: number
  model: string | null
  artifact_path: string | null
}

export interface Stats {
  agent_count: number
  online_agents: number
  busy_agents: number
  offline_agents: number
  business_line_count: number
  running_lines: number
  error_lines: number
  today_cost_usd: number
  month_cost_usd: number
  total_executions: number
  failed_executions: number
  pending_alerts: number
}

export interface CronJob {
  id: string
  name: string
  agent_id: string | null
  business_line_id: string | null
  schedule_expr: string | null
  enabled: boolean
  last_run_at: string | null
  last_status: string | null
  consecutive_errors: number
  last_error: string | null
}

export interface Alert {
  id: number
  severity: string | null
  title: string
  description: string | null
  source: string | null
  resolved: boolean
  created_at: string | null
}

export interface CostSummary {
  group: string
  items: CostSummaryItem[]
}

export interface CostSummaryItem {
  name: string
  total_calls: number
  total_cost_usd: number
  avg_cost_per_call: number
}

export interface Artifact {
  id: string
  run_id: string | null
  business_line: string
  date: string
  artifact_path: string
  word_count: number
  file_size_bytes: number
  file_type: string | null
  artifact_status: string
  cost_usd: number
}

// ── Phase 5: Tasks & Command ──

export interface Task {
  id: number
  title: string
  description: string | null
  agent_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled'
  priority: string
  source: string | null
  required_skills: string | null
  success_criteria: string | null
  failure_reason: string | null
  result_summary: string | null
  error_message: string | null
  created_at: string | null
  updated_at: string | null
}

export interface TaskMessage {
  id: number
  task_id: number
  role: string
  content: string
  msg_metadata: string | null
  created_at: string | null
}

export interface CommandRequest {
  instruction: string
  agent_id: string
  priority?: string
  required_skills?: string | null
  success_criteria?: string | null
}

export interface CommandResponse {
  task: Task
  message: string
}

// ── Phase 0.4: Chat Panel ──

export interface ChatRequest {
  message: string
  session_id?: number | null
}

export interface ChatResponse {
  reply: string
  session_id: number
  tokens_used: number | null
}

export interface ChatSessionItem {
  id: number
  title: string
  status: string
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export interface ChatMessage {
  id: number
  role: string
  content: string
  metadata: string | null
  created_at: string | null
}

export interface ChatSessionDetail {
  session: {
    id: number
    title: string
    status: string
    created_at: string | null
    updated_at: string | null
  }
  messages: ChatMessage[]
}
