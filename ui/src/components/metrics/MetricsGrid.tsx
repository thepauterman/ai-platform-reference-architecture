import { useCallback, useState, useEffect, useRef } from 'react'
import { fetchMetrics } from '../../api/client'
import type { MetricsResponse } from '../../api/types'
import MetricCard from './MetricCard'

function fmt(n: number, decimals = 0): string {
  return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

interface Props {
  queryVersion?: number
}

export default function MetricsGrid({ queryVersion = 0 }: Props) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const prevVersion = useRef(queryVersion)

  const loadMetrics = useCallback(async () => {
    try {
      const data = await fetchMetrics()
      setMetrics(data)
    } catch { /* ignore */ }
  }, [])

  // Initial load + polling
  useEffect(() => {
    loadMetrics()
    const id = setInterval(loadMetrics, 10000)
    return () => clearInterval(id)
  }, [loadMetrics])

  // Refresh when queryVersion changes
  useEffect(() => {
    if (queryVersion > prevVersion.current) {
      prevVersion.current = queryVersion
      const t = setTimeout(loadMetrics, 500)
      return () => clearTimeout(t)
    }
  }, [queryVersion, loadMetrics])

  const cards = metrics
    ? [
        { label: 'Total Requests', value: fmt(metrics.total_requests), delta: metrics.deltas.requests_per_second },
        { label: 'Success Rate', value: `${fmt(metrics.success_rate, 1)}%`, delta: metrics.deltas.success_rate },
        { label: 'P95 Latency', value: fmt(metrics.p95_latency_ms), unit: 'ms', delta: metrics.deltas.p95_latency_ms },
        { label: 'Cost / Request', value: `$${metrics.cost_per_request.toFixed(6)}`, delta: metrics.deltas.cost_per_request },
        { label: 'Total Tokens', value: fmt(metrics.total_tokens), delta: metrics.deltas.total_tokens },
        { label: 'Used Models', value: String(metrics.active_models), delta: metrics.deltas.active_models },
      ]
    : [
        { label: 'Total Requests', value: '—', delta: '+0.0%' },
        { label: 'Success Rate', value: '—', delta: '+0.0%' },
        { label: 'P95 Latency', value: '—', unit: 'ms', delta: '+0.0%' },
        { label: 'Cost / Request', value: '—', delta: '+0.0%' },
        { label: 'Total Tokens', value: '—', delta: '+0.0%' },
        { label: 'Used Models', value: '—', delta: '+0.0%' },
      ]

  return (
    <div id="metrics" className="mx-8 mt-6">
      <h2 className="text-sm font-medium uppercase tracking-widest text-white mb-3">Metrics</h2>
      <div className="flex gap-4">
        {cards.map(card => (
          <MetricCard key={card.label} {...card} />
        ))}
      </div>
    </div>
  )
}
