import type { DemoOffer, DemoRun } from '@/types/demoSpine'

const BASE = '/api/v1/vs001/demo-spine'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  const response = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || `Demo Spine API ${response.status}`)
  }
  return response.json()
}

export function listDemoOffers() {
  return request<{ offers: DemoOffer[] }>('/offers')
}

export function listDemoRuns() {
  return request<{ runs: DemoRun[] }>('/runs')
}

export function createDemoRun(body: { offer_id: string; founder_goal: string }) {
  return request<DemoRun>('/runs', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getDemoRun(runId: string) {
  return request<DemoRun>(`/runs/${runId}`)
}

export function advanceDemoRun(runId: string) {
  return request<DemoRun>(`/runs/${runId}/advance`, { method: 'POST' })
}

export function decideDemoRun(runId: string, decision: 'go' | 'no_go') {
  return request<DemoRun>(`/runs/${runId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  })
}
