export interface QueryRequest {
  prompt: string
  user_id?: string
  session_id?: string
}

export interface QueryResponse {
  response: string | null
  model_used: string | null
  policy_checked: boolean
  request_id: string | null
  classification: string | null
  fallback_used: boolean | null
}

export interface PipelineStep {
  step: string
  status: string
  detail: string
  latency_ms: number
}

export interface AuditMetadata {
  provider?: string
  model_name?: string
  classification?: string
  pii_detected?: string[]
  fallback_used?: boolean
  tokens_used?: number
  total_latency_ms?: number
  pipeline_trace?: PipelineStep[]
  reason?: string
  error?: string
}

export interface AuditEntry {
  id: number
  request_id: string
  timestamp: string
  timestamp_pt: string
  prompt: string
  outcome: 'approved' | 'blocked' | 'error'
  metadata: AuditMetadata
}

export interface MetricsResponse {
  requests_per_second: number
  success_rate: number
  p95_latency_ms: number
  cost_per_request: number
  active_models: number
  providers: string[]
  total_tokens: number
  total_requests: number
  approved: number
  blocked: number
  errors: number
  pii_detected_count: number
  deltas: {
    requests_per_second: string
    success_rate: string
    p95_latency_ms: string
    cost_per_request: string
    active_models: string
    total_tokens: string
  }
}
