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
  context?: {
    page: string
    summary?: string
    filters?: string
  } | null
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

// ── v0.2 Company Loop MVP ──

export interface TaskPoolItem {
  id: number
  title: string
  description: string | null
  business_line: string | null
  source: string            // alert / command / manual / cron
  source_id: string | null
  status: string            // draft / ready / approval_required / approved / running / review / done / blocked / cancelled
  priority: string          // low / medium / high / critical
  risk_level: string        // low / medium / high
  assigned_agent: string | null
  context_pack_id: number | null
  requires_approval: boolean
  acceptance_criteria: string | null
  result_summary: string | null
  error_message: string | null
  cost_usd: number
  failure_reason: string | null
  created_at: string | null
  updated_at: string | null
  completed_at: string | null
}

export interface ContextPack {
  id: number
  task_id: number
  founder_intent: string | null
  business_line_state: string | null
  related_runs: string | null
  related_artifacts: string | null
  known_failures: string | null
  relevant_rules: string | null
  constraints: string | null
  forbidden_actions: string | null
  budget_limit: number | null
  acceptance_criteria: string | null
  referenced_knowledge: string | null
  auto_generated: boolean
  created_at: string | null
  updated_at: string | null
}

export interface ApprovalItem {
  id: number
  target_type: string
  target_id: number
  risk_level: string
  reason: string | null
  founder_decision: string | null
  founder_notes: string | null
  decision_context: string | null
  status: string
  approved_at: string | null
  created_at: string | null
}

// ── v0.3 CEO Agent Lite ──

export interface GoalSession {
  id: number
  source_channel: string
  raw_goal: string
  client_request_id: string | null
  interpreted_goal: string | null
  goal_type: string | null
  business_line: string | null
  priority: string
  risk_level: string
  status: string            // draft / decomposed / committed / cancelled / failed
  decomposition_json: string | null
  task_ids_json: string | null
  approval_ids_json: string | null
  model_used: string | null
  confidence: number | null
  schema_version: string
  error_message: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CeoActionLog {
  id: number
  source_channel: string
  raw_user_message: string
  intent_type: string        // goal_intake / approval_action
  target_type: string | null
  target_id: number | null
  action_taken: string | null
  payload_json: string | null
  result_status: string      // success / failed / ambiguous / cancelled
  result_summary: string | null
  confidence: number | null
  requires_confirmation: boolean
  confirmed_by_founder: boolean
  created_at: string | null
}

export interface ApprovalDecisionRequest {
  founder_decision: string   // approved / revised / rejected / deferred
  founder_notes?: string
}

export interface ReviewItem {
  id: number
  task_id: number
  result: string             // pass / revision_required / blocked
  artifact_id: string | null
  review_notes: string | null
  next_action: string | null
  reviewed_by: string
  created_at: string | null
}

export interface LearningCandidate {
  id: number
  source_type: string
  source_id: string | null
  source_summary: string | null
  candidate_type: string
  summary: string | null
  recommendation: string | null
  approval_status: string
  approved_by: string | null
  approved_at: string | null
  created_at: string | null
}

export interface LoopStats {
  total_tasks: number
  alert_pooled_count: number
  approval_rate: number
  review_distribution: Record<string, number>
  candidate_count: number
  candidate_approved_count: number
  pending_approval_tasks: number
  pending_candidates: number
  recent_task_trend: { date: string; count: number }[]
}

export interface AlertToTaskResult {
  pooled: number
  skipped: number
  errors: { alert_id: number; reason: string }[]
}

// ── OrgMemory (v0.4) ──
export interface OrgMemoryEntry {
  id: number
  memory_type: string
  title: string
  summary: string | null
  content: string | null
  business_line: string | null
  tags: string | null
  source_type: string | null
  source_id: string | null
  source_candidate_id: number | null
  source_task_id: number | null
  source_review_id: number | null
  source_goal_session_id: number | null
  confidence: number | null
  status: string
  version: number
  supersedes_memory_id: number | null
  created_at: string | null
  updated_at: string | null
}

export interface MemorySearchResult {
  id: number
  memory_type: string
  title: string
  summary: string | null
  snippet: string | null
  business_line: string | null
  tags: string | null
  status: string
  version: number
  source_type: string | null
  source_id: string | null
  source_candidate_id: number | null
  source_task_id: number | null
  source_review_id: number | null
  source_goal_session_id: number | null
  created_at: string | null
}

export interface KnowledgeProposal {
  id: number
  source_candidate_id: number
  proposal_type: string
  title: string
  summary: string | null
  structured_content: string | null
  target_memory_type: string
  business_line: string | null
  status: string
  org_memory_id: number | null
  committed_at: string | null
  founder_notes: string | null
  created_at: string | null
}

export interface RecalledMemory {
  memory_id: number
  title: string
  summary: string | null
  memory_type: string
  confidence: number
}

export interface MemoryRecallResponse {
  memories: RecalledMemory[]
  recall_query: string
  total: number
}
  errors: { alert_id: number; reason: string }[]
}
