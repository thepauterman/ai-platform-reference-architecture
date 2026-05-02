interface Props {
  label: string
  value: string
  delta: string
  unit?: string
}

export default function MetricCard({ label, value, delta, unit }: Props) {
  const isPositive = delta.startsWith('+')
  const isNeutral = delta === '+0.0%'
  const deltaColor = isNeutral ? 'text-muted' : isPositive ? 'text-accent-green' : 'text-accent-red'

  return (
    <div className="flex-1 rounded-lg border border-card-border bg-card p-5">
      <div className="text-base text-muted mb-2">{label}</div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-semibold text-white">{value}</span>
        {unit && <span className="text-base text-muted">{unit}</span>}
      </div>
      <div className={`text-base mt-1.5 ${deltaColor}`}>
        {delta} <span className="text-muted">vs 1h ago</span>
      </div>
    </div>
  )
}
