// Use relative path — Next.js rewrites /api/v1/* to the backend
const API_BASE = ''

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API ${path}: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// ── Stats ──
export async function getStats() {
  return fetchAPI<import('../types/api').Stats>('/api/v1/stats')
}

// ── Agents ──
export async function getAgents(status?: string) {
  const q = status ? `?status=${status}` : ''
  return fetchAPI<import('../types/api').Agent[]>(`/api/v1/agents${q}`)
}

export async function getAgent(name: string) {
  return fetchAPI<import('../types/api').Agent>(`/api/v1/agents/${name}`)
}

// ── Business Lines ──
export async function getBusinessLines() {
  return fetchAPI<import('../types/api').BusinessLine[]>('/api/v1/business-lines')
}

export async function getBusinessLineRuns(lineId: string, limit = 20) {
  return fetchAPI<import('../types/api').ExecutionRecord[]>(
    `/api/v1/business-lines/${lineId}/runs?limit=${limit}`
  )
}

// ── Runs ──
export async function getRuns(params?: {
  date_from?: string
  date_to?: string
  business_line?: string
  result?: string
  limit?: number
  offset?: number
}) {
  const q = new URLSearchParams()
  if (params?.date_from) q.set('date_from', params.date_from)
  if (params?.date_to) q.set('date_to', params.date_to)
  if (params?.business_line) q.set('business_line', params.business_line)
  if (params?.result) q.set('result', params.result)
  if (params?.limit) q.set('limit', String(params.limit))
  if (params?.offset) q.set('offset', String(params.offset))
  return fetchAPI<import('../types/api').ExecutionRecord[]>(`/api/v1/runs?${q}`)
}

export async function getRun(runId: string) {
  return fetchAPI<import('../types/api').ExecutionRecord>(`/api/v1/runs/${runId}`)
}

// ── Costs ──
export async function getCosts(groupBy = 'model') {
  return fetchAPI<import('../types/api').CostSummary>(`/api/v1/costs?group_by=${groupBy}`)
}

// ── Cron Jobs ──
export async function getCronJobs() {
  return fetchAPI<import('../types/api').CronJob[]>('/api/v1/cron-jobs')
}

// ── Alerts ──
export async function getAlerts(severity?: string, resolved?: boolean) {
  const q = new URLSearchParams()
  if (severity) q.set('severity', severity)
  if (resolved !== undefined) q.set('resolved', String(resolved))
  return fetchAPI<import('../types/api').Alert[]>(`/api/v1/alerts?${q}`)
}

// ── Artifacts ──
export async function getArtifacts(businessLine?: string, date?: string) {
  const q = new URLSearchParams()
  if (businessLine) q.set('business_line', businessLine)
  if (date) q.set('date', date)
  return fetchAPI<import('../types/api').Artifact[]>(`/api/v1/artifacts?${q}`)
}

// ── Refresh ──
export async function refreshData() {
  return fetchAPI<{ status: string; refreshed_at: string; results: Record<string, number> }>(
    '/api/v1/refresh', { method: 'POST' }
  )
}

// ── Tasks ──
export async function getTasks(params?: {
  status?: string
  agent_id?: string
  limit?: number
  offset?: number
}) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.agent_id) q.set('agent_id', params.agent_id)
  if (params?.limit) q.set('limit', String(params.limit))
  if (params?.offset) q.set('offset', String(params.offset))
  return fetchAPI<import('../types/api').Task[]>(`/api/v1/tasks?${q}`)
}

export async function getTask(taskId: number) {
  return fetchAPI<import('../types/api').Task>(`/api/v1/tasks/${taskId}`)
}

export async function createTask(data: {
  title: string
  description?: string
  agent_id?: string
  priority?: string
  required_skills?: string | null
  success_criteria?: string | null
}) {
  return fetchAPI<import('../types/api').Task>('/api/v1/tasks', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateTask(taskId: number, data: {
  status?: string
  result_summary?: string
  error_message?: string
  failure_reason?: string
}) {
  return fetchAPI<import('../types/api').Task>(`/api/v1/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function cancelTask(taskId: number) {
  return fetchAPI<import('../types/api').Task>(`/api/v1/tasks/${taskId}/cancel`, { method: 'POST' })
}

export async function getTaskMessages(taskId: number) {
  return fetchAPI<import('../types/api').TaskMessage[]>(`/api/v1/tasks/${taskId}/messages`)
}

export async function sendCommand(data: import('../types/api').CommandRequest) {
  return fetchAPI<import('../types/api').CommandResponse>('/api/v1/command', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function patchAgent(name: string, data: { skills?: string; capabilities?: string; role?: string; status?: string }) {
  return fetchAPI<{ status: string; agent: string; updated_fields: string[] }>(
    `/api/v1/agents/${name}`, { method: 'PATCH', body: JSON.stringify(data) }
  )
}

export async function getSkillsMap() {
  return fetchAPI<{
    total_skills: number
    total_agents_with_skills: number
    skills: { skill: string; agent_count: number; agents: string[]; coverage: string }[]
    task_gaps: { skill: string; task_id: number; task_title: string }[]
    agent_skills: Record<string, string[]>
  }>('/api/v1/skills')
}

export async function getCostTrend(days = 7) {
  return fetchAPI<{
    total: { date: string; cost_usd: number; input_tokens: number; output_tokens: number; calls: number }[]
    by_agent: Record<string, { date: string; cost_usd: number; input_tokens: number; output_tokens: number; calls: number }[]>
    days: number
  }>(`/api/v1/costs/trend?days=${days}`)
}

// ── Phase 7: Analysis & Retry ──

export async function retryTask(taskId: number) {
  return fetchAPI<import('../types/api').Task>(`/api/v1/tasks/${taskId}/retry`, { method: 'POST' })
}

export async function getFailureAnalysis() {
  return fetchAPI<{
    total_failed: number
    total_tasks: number
    failure_rate: number
    by_reason: { reason: string; count: number }[]
    by_agent: { agent: string; count: number }[]
    by_skill: { skill: string; count: number }[]
    daily: { date: string; count: number }[]
    recent_failures: { task_id: number; title: string; agent_id: string; failure_reason: string; error_message: string | null; created_at: string | null }[]
    recommendations: { type: string; reason?: string; agent?: string; count?: number; fail_rate?: number; suggestion: string }[]
  }>('/api/v1/analysis/failures')
}

export async function getGapAnalysis() {
  return fetchAPI<{
    total_gap_skills: number
    recommendations: { skill: string; occurrence_count: number; severity: string; suggestion: string }[]
  }>('/api/v1/analysis/gaps')
}

// ── Phase 0.4: Chat Panel ──

export async function sendChatMessage(data: import('../types/api').ChatRequest): Promise<import('../types/api').ChatResponse> {
  return fetchAPI<import('../types/api').ChatResponse>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getChatSessions(limit = 50): Promise<import('../types/api').ChatSessionItem[]> {
  return fetchAPI<import('../types/api').ChatSessionItem[]>(`/api/v1/chat/sessions?limit=${limit}`)
}

export async function getChatSession(sessionId: number): Promise<import('../types/api').ChatSessionDetail> {
  return fetchAPI<import('../types/api').ChatSessionDetail>(`/api/v1/chat/sessions/${sessionId}`)
}

export async function deleteChatSession(sessionId: number): Promise<{ status: string; session_id: number }> {
  return fetchAPI<{ status: string; session_id: number }>(`/api/v1/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  })
}

// ── v0.2 Company Loop MVP ──

export async function getTaskPool(params?: {
  status?: string
  business_line?: string
  source?: string
  priority?: string
}) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.business_line) q.set('business_line', params.business_line)
  if (params?.source) q.set('source', params.source)
  if (params?.priority) q.set('priority', params.priority)
  return fetchAPI<import('../types/api').TaskPoolItem[]>(`/api/v1/task-pool?${q}`)
}

export async function getTaskPoolItem(taskId: number) {
  return fetchAPI<import('../types/api').TaskPoolItem>(`/api/v1/task-pool/${taskId}`)
}

export async function createTaskPoolItem(data: Partial<import('../types/api').TaskPoolItem>) {
  return fetchAPI<import('../types/api').TaskPoolItem>('/api/v1/task-pool', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateTaskPoolItem(taskId: number, data: Record<string, unknown>) {
  return fetchAPI<import('../types/api').TaskPoolItem>(`/api/v1/task-pool/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function getContextPack(taskId: number) {
  return fetchAPI<import('../types/api').ContextPack>(`/api/v1/task-pool/${taskId}/context-pack`)
}

export async function upsertContextPack(taskId: number, data: Partial<import('../types/api').ContextPack>) {
  return fetchAPI<import('../types/api').ContextPack>(`/api/v1/task-pool/${taskId}/context-pack`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getApprovals(params?: { status?: string; target_type?: string }) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.target_type) q.set('target_type', params.target_type)
  return fetchAPI<import('../types/api').ApprovalItem[]>(`/api/v1/approvals?${q}`)
}

export async function createApproval(data: { target_type: string; target_id: number; risk_level?: string; reason?: string }) {
  return fetchAPI<import('../types/api').ApprovalItem>('/api/v1/approvals', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function decideApproval(approvalId: number, data: import('../types/api').ApprovalDecisionRequest) {
  return fetchAPI<import('../types/api').ApprovalItem>(`/api/v1/approvals/${approvalId}/decide`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function getReview(reviewId: number) {
  return fetchAPI<import('../types/api').ReviewItem>(`/api/v1/reviews/${reviewId}`)
}

export async function createReview(data: { task_id: number; result: string; artifact_id?: string; review_notes?: string; next_action?: string }) {
  return fetchAPI<import('../types/api').ReviewItem>('/api/v1/reviews', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getLearningCandidates(params?: { status?: string; source_type?: string; candidate_type?: string }) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.source_type) q.set('source_type', params.source_type)
  if (params?.candidate_type) q.set('candidate_type', params.candidate_type)
  return fetchAPI<import('../types/api').LearningCandidate[]>(`/api/v1/learning-candidates?${q}`)
}

export async function createLearningCandidate(data: { source_type: string; source_id?: string; source_summary?: string; candidate_type: string; summary?: string; recommendation?: string }) {
  return fetchAPI<import('../types/api').LearningCandidate>('/api/v1/learning-candidates', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function decideLearningCandidate(candidateId: number, data: { approval_status: string; approved_by?: string }) {
  return fetchAPI<import('../types/api').LearningCandidate>(`/api/v1/learning-candidates/${candidateId}/decide`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function getLoopStats() {
  return fetchAPI<import('../types/api').LoopStats>('/api/v1/loop-stats')
}

export async function triggerAlertToTask() {
  return fetchAPI<import('../types/api').AlertToTaskResult>('/api/v1/alert-to-task', { method: 'POST' })
}

// ── v0.3 CEO Agent Lite ──

export async function getGoalSessions(params?: {
  status?: string
  source_channel?: string
  business_line?: string
}) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.source_channel) q.set('source_channel', params.source_channel)
  if (params?.business_line) q.set('business_line', params.business_line)
  return fetchAPI<import('../types/api').GoalSession[]>(`/api/v1/ceo/goal-sessions?${q}`)
}

export async function createGoalSession(data: { raw_goal: string; source_channel?: string; business_line?: string }) {
  return fetchAPI<import('../types/api').GoalSession>('/api/v1/ceo/goal-sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getGoalSession(id: number) {
  return fetchAPI<import('../types/api').GoalSession>(`/api/v1/ceo/goal-sessions/${id}`)
}

export async function getCeoActionLogs(params?: {
  intent_type?: string
  target_type?: string
  result_status?: string
}) {
  const q = new URLSearchParams()
  if (params?.intent_type) q.set('intent_type', params.intent_type)
  if (params?.target_type) q.set('target_type', params.target_type)
  if (params?.result_status) q.set('result_status', params.result_status)
  return fetchAPI<import('../types/api').CeoActionLog[]>(`/api/v1/ceo/action-logs?${q}`)
}

// ── Memory (v0.4) ──
export async function getMemoryEntries(params?: { business_line?: string; memory_type?: string; status?: string }) {
  const q = new URLSearchParams()
  if (params?.business_line) q.set('business_line', params.business_line)
  if (params?.memory_type) q.set('memory_type', params.memory_type)
  if (params?.status) q.set('status', params.status)
  return fetchAPI<import('../types/api').OrgMemoryEntry[]>(`/api/v1/memory/entries${q.toString() ? '?' + q.toString() : ''}`)
}

export async function searchMemory(q: string, business_line?: string, memory_type?: string) {
  const params = new URLSearchParams({ q })
  if (business_line) params.set('business_line', business_line)
  if (memory_type) params.set('memory_type', memory_type)
  return fetchAPI<import('../types/api').MemorySearchResult[]>(`/api/v1/memory/search?${params.toString()}`)
}

export async function getKnowledgeProposals(status?: string) {
  const q = status ? `?status=${status}` : ''
  return fetchAPI<import('../types/api').KnowledgeProposal[]>(`/api/v1/memory/knowledge-proposals${q}`)
}

export async function decideProposal(id: number, decision: { status: string; founder_notes?: string }) {
  return fetchAPI<import('../types/api').KnowledgeProposal>(`/api/v1/memory/knowledge-proposals/${id}/decide`, {
    method: 'PATCH',
    body: JSON.stringify(decision),
  })
}

// ── v0.6 Runtime Layer MVP ──

export async function getRuntimes() {
  return fetchAPI<import('../types/api').RuntimeInfo[]>('/api/v1/runtimes')
}

export async function refreshRuntimes() {
  return fetchAPI<import('../types/api').RuntimeRefreshItem[]>('/api/v1/runtimes/refresh', { method: 'POST' })
}

export async function getRuntimeCapabilities(runtimeId: string) {
  return fetchAPI<{ runtime_id: string; capabilities: import('../types/api').RuntimeCapability[] }>(
    `/api/v1/runtimes/${runtimeId}/capabilities`
  )
}