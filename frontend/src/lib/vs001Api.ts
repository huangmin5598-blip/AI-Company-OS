import type {
  PilotAssetEnvelope,
  PilotStatus,
  WorkOrderEnvelope,
} from '@/types/vs001'

const BASE = '/api/v1/vs001'

async function request<T>(
  path: string,
  options: RequestInit = {},
  idempotencyKey?: string,
): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (idempotencyKey) headers.set('Idempotency-Key', idempotencyKey)
  const response = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || `Pilot API ${response.status}`)
  }
  return response.json()
}

export function pilotStatus() {
  return request<PilotStatus>('/status')
}

export function listPilotWorkOrders() {
  return request<{ work_orders: WorkOrderEnvelope[] }>('/work-orders')
}

export function createPilotWorkOrder(body: {
  skill_id: string
  task_type: string
  input_context: string
  expected_output: string
}) {
  return request<WorkOrderEnvelope>(
    '/work-orders',
    { method: 'POST', body: JSON.stringify(body) },
    crypto.randomUUID(),
  )
}

export function requestPilotApproval(workOrderId: string) {
  return request<WorkOrderEnvelope>(
    `/work-orders/${workOrderId}/request-approval`,
    { method: 'POST' },
    crypto.randomUUID(),
  )
}

export function approvePilotWorkOrder(workOrderId: string) {
  return request<WorkOrderEnvelope>(
    `/work-orders/${workOrderId}/approve`,
    { method: 'POST' },
    crypto.randomUUID(),
  )
}

export function executePilotWorkOrder(
  workOrderId: string,
  body: { heading: string; body: string },
) {
  return request<WorkOrderEnvelope>(
    `/work-orders/${workOrderId}/execute`,
    { method: 'POST', body: JSON.stringify(body) },
    crypto.randomUUID(),
  )
}

export function reviewPilotWorkOrder(workOrderId: string) {
  return request<WorkOrderEnvelope>(
    `/work-orders/${workOrderId}/review`,
    { method: 'POST', body: JSON.stringify({ decision: 'passed' }) },
    crypto.randomUUID(),
  )
}

export function listPilotAssets() {
  return request<{ assets: PilotAssetEnvelope[] }>('/assets')
}

export function getPilotAsset(assetId: string, includeContent = false) {
  return request<PilotAssetEnvelope>(
    `/assets/${assetId}${includeContent ? '/content' : ''}`,
  )
}

export function approvePilotAsset(assetId: string) {
  return request<PilotAssetEnvelope>(
    `/assets/${assetId}/approve`,
    { method: 'POST' },
    crypto.randomUUID(),
  )
}
