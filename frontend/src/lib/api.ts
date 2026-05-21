// Use relative path — Next.js rewrites /api/v1/* to the backend
const API_BASE = ''

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
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