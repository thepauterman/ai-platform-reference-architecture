import { Eye } from 'lucide-react'

export default function ObservabilityBar() {
  return (
    <div className="mx-8 mt-4 flex items-center gap-4 rounded-lg border border-card-border bg-card px-6 py-7">
      <Eye className="w-6 h-6 text-muted" />
      <span className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-accent-green animate-pulse" />
        <span className="text-base font-medium uppercase tracking-wider text-accent-green">Running</span>
      </span>
      <span className="text-lg font-medium text-white">Observability</span>
      <div className="flex items-center gap-3 ml-3 text-base text-muted">
        <span>Audit Log</span>
        <span>·</span>
        <span>Tracing</span>
        <span>·</span>
        <span>Metrics</span>
      </div>
    </div>
  )
}
