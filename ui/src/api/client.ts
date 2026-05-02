import type { QueryRequest, QueryResponse, AuditEntry, MetricsResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail?.reason || body?.detail || `API error: ${res.status}`)
  }
  return res.json()
}

export async function queryGateway(request: QueryRequest): Promise<QueryResponse> {
  return apiFetch<QueryResponse>('/query', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function fetchAuditLogs(limit = 20): Promise<AuditEntry[]> {
  const data = await apiFetch<{ logs: AuditEntry[] }>(`/audit?limit=${limit}`)
  return data.logs
}

export async function fetchAuditDetail(requestId: string): Promise<AuditEntry> {
  return apiFetch<AuditEntry>(`/audit/${requestId}`)
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  return apiFetch<MetricsResponse>('/metrics')
}

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}
