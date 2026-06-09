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
    result_ref: string | null
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
    result_ref: string
    result_payload_hash: string
    scratch_root: string
  }
}
