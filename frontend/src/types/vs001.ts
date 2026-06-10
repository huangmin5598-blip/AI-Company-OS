export type PilotStatus = {
  mode: 'os_governed_pilot'
  authority: 'pilot_non_authoritative'
  database_path: string
  banner: string
  operational_database: {
    expected_sha256: string
    actual_sha256: string
    matches: boolean
  }
}

export type WorkOrderEnvelope = {
  data: {
    work_order_id: string
    skill_id: string
    task_type: string
    input_context: string
    expected_output: string
    canonical_state: string
    legacy_status: string | null
    row_version: number
    created_at: string | null
    terminal_at: string | null
    result_summary?: string
  }
  provenance: {
    authority: string
    classification: string
    evidence_tier: string
    resolution_status: string
    reason_codes: string[]
    source_system: string
    source_key: string
    source_hash: string
    evidence_refs: Array<Record<string, string>>
    anomaly_refs: string[]
  }
  tenant_id: string
  workspace_id: string
  governance?: {
    mode: string
    authority: string
    policy: Record<string, unknown>
  }
  latest_approval?: {
    approval_id: string
    decision: string
    row_version: number
    requested_by: string
    decided_by: string | null
  } | null
  latest_attempt?: {
    attempt_id: string
    state: string
    row_version: number
    result_payload_hash: string | null
  } | null
  latest_review?: {
    review_id: string
    state: string
    row_version: number
    reviewer_id: string | null
    findings: Array<Record<string, unknown>>
  } | null
  execution?: {
    attempt_id: string
    review_id: string
    result_markdown: string
    result_payload_hash: string
    artifact_id: string
    artifact_ref: string
  }
  assets?: Array<{
    asset_id: string
    status: 'candidate' | 'approved'
    title: string
    authority: 'pilot_non_authoritative'
    visibility: 'restricted'
    approval_id: string | null
  }>
}

export type PilotAssetEnvelope = {
  asset: {
    asset_id: string
    title: string
    asset_type: string
    status: 'candidate' | 'approved'
    version: number
    source_work_order_id: string
    source_review_id: string
    content_ref: string
    public_safe_ref: null
    visibility: 'restricted'
    authority: 'pilot_non_authoritative'
    source_path: 'os_governed_work_review'
    source_authority: 'pilot_non_authoritative'
    row_version: number
    approval_id: string | null
  }
  artifact_refs: Array<{
    artifact_id: string
    content_hash: string
    media_type: string
    size_bytes: number
  }>
  approval: {
    approval_id: string
    decision: string
    row_version: number
    decided_by: string | null
  } | null
  content: {
    text: string
    media_type: string
    content_hash: string
    size_bytes: number
  } | null
  governance: {
    authority: 'pilot_non_authoritative'
    visibility: 'restricted'
    public_safe: false
    official_asset_center: false
  }
}
