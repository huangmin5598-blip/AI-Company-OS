import type {
  RealWorkbenchRun,
  RealWorkbenchTemplate,
} from '@/types/realWorkbench'

const BASE = '/api/v1/vs001/real-workbench'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  const response = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || `Real Workbench API ${response.status}`)
  }
  return response.json()
}

export function listRealWorkbenchTemplates() {
  return request<{ templates: RealWorkbenchTemplate[] }>('/templates')
}

export function listRealWorkbenchRuns() {
  return request<{ runs: RealWorkbenchRun[] }>('/runs')
}

export function createRealWorkbenchRun(body: {
  product_line_id: string
  founder_goal: string
}) {
  return request<RealWorkbenchRun>('/runs', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getRealWorkbenchRun(runId: string) {
  return request<RealWorkbenchRun>(`/runs/${runId}`)
}
