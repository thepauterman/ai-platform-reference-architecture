import { useCallback, useState, useEffect, useRef } from 'react'
import { fetchAuditLogs, fetchAuditDetail } from '../../api/client'
import type { AuditEntry, PipelineStep } from '../../api/types'

const statusColor: Record<string, string> = {
  'OK': 'text-accent-green',
  'PASS': 'text-accent-green',
  '200 OK': 'text-accent-green',
  'DONE': 'text-accent-green',
  'FAIL': 'text-accent-red',
  'BLOCKED': 'text-accent-red',
  'ERROR': 'text-accent-red',
  'FALLBACK': 'text-accent-yellow',
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('en-US', { hour12: false })
  } catch {
    return ts.slice(11, 19)
  }
}

function formatDetail(step: PipelineStep): string {
  return step.detail
}

interface Props {
  onTraceLoaded?: (steps: PipelineStep[]) => void
  queryVersion?: number
}

export default function AuditLog({ onTraceLoaded, queryVersion = 0 }: Props) {
  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<AuditEntry | null>(null)
  const prevVersion = useRef(queryVersion)

  const loadLogs = useCallback(async () => {
    try {
      const data = await fetchAuditLogs(10)
      setLogs(data)
      return data
    } catch {
      return []
    }
  }, [])

  // Initial load + polling
  useEffect(() => {
    loadLogs()
    const id = setInterval(loadLogs, 5000)
    return () => clearInterval(id)
  }, [loadLogs])

  // Refresh when queryVersion changes (new query completed)
  useEffect(() => {
    if (queryVersion > prevVersion.current) {
      prevVersion.current = queryVersion
      // Delay slightly to let backend write the audit log
      const t = setTimeout(async () => {
        const freshLogs = await loadLogs()
        if (freshLogs.length > 0) {
          handleSelect(freshLogs[0].request_id)
        }
      }, 300)
      return () => clearTimeout(t)
    }
  }, [queryVersion, loadLogs])

  const handleSelect = async (requestId: string) => {
    setSelectedId(requestId)
    try {
      const entry = await fetchAuditDetail(requestId)
      setDetail(entry)
      if (entry.metadata?.pipeline_trace) {
        onTraceLoaded?.(entry.metadata.pipeline_trace)
      }
    } catch {
      setDetail(null)
    }
  }

  // Auto-select first log entry on initial load
  if (logs.length > 0 && !selectedId) {
    handleSelect(logs[0].request_id)
  }

  const trace = detail?.metadata?.pipeline_trace || []
  const timestamp = detail?.timestamp || ''
  const shortId = selectedId ? selectedId.slice(0, 8) : '--------'

  return (
    <div id="audit" className="mx-8 mt-6">
      <div className="flex items-center gap-3 mb-3">
        <h2 className="text-sm font-medium uppercase tracking-widest text-white">Audit Log</h2>
        <span className="text-sm text-muted">·</span>
        {logs.length > 0 ? (
          <select
            value={selectedId || ''}
            onChange={(e) => handleSelect(e.target.value)}
            className="bg-card border border-card-border rounded px-2.5 py-1 text-sm text-muted focus:outline-none focus:border-accent-blue"
          >
            {logs.map(log => (
              <option key={log.request_id} value={log.request_id}>
                REQ_{log.request_id.slice(0, 8)} - {log.outcome}
              </option>
            ))}
          </select>
        ) : (
          <span className="text-sm text-muted">No logs yet</span>
        )}
      </div>

      <div className="rounded-lg border border-card-border bg-terminal font-mono text-base">
        <div className="px-5 py-3 border-b border-card-border/50">
          <span className="text-muted">$ </span>
          <span className="text-white">show audit log req_{shortId}</span>
        </div>

        <div className="px-5 py-4 space-y-1.5">
          {trace.length > 0 ? (
            trace.map((step, i) => (
              <div
                key={`${selectedId}-${i}`}
                className="flex items-center justify-between animate-fade-in"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-baseline gap-4">
                  <span className="text-muted text-base">{formatTime(timestamp)}</span>
                  <span className="text-white w-48 inline-block">{step.step}</span>
                  <span className={statusColor[step.status] || 'text-accent-cyan'}>
                    {formatDetail(step)}
                  </span>
                </div>
                <span className="text-muted text-base">{step.latency_ms}ms</span>
              </div>
            ))
          ) : (
            <div className="text-muted text-sm py-4 text-center">
              {logs.length > 0 ? 'Loading trace...' : 'Send a query to see the audit log'}
            </div>
          )}
        </div>

        {detail && (
          <div className="px-5 py-3 border-t border-card-border/50 text-sm text-muted">
            Request ID: {detail.request_id}
            {detail.metadata?.total_latency_ms && (
              <span> · Total: {detail.metadata.total_latency_ms}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
