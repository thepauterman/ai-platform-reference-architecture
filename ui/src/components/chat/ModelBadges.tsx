interface BadgeProps {
  label: string
  value: string
  color: string
}

function Badge({ label, value, color }: BadgeProps) {
  return (
    <div className="text-center">
      <div className="text-sm text-muted uppercase tracking-wider">{label}</div>
      <div className={`text-base font-medium ${color}`}>{value}</div>
    </div>
  )
}

interface Props {
  model?: string
  routing?: string
  policyStatus?: string
  piiEnabled?: boolean
  auditOn?: boolean
}

export default function ModelBadges({
  model = 'gpt-4o',
  routing = 'auto-route',
  policyStatus = 'enforced',
  piiEnabled = true,
  auditOn = true,
}: Props) {
  return (
    <div className="flex items-center justify-between px-6 py-5 border-b border-card-border">
      <Badge label="Model" value={model} color="text-accent-green" />
      <Badge label="Routing" value={routing} color="text-accent-orange" />
      <Badge label="Policy" value={policyStatus} color="text-accent-green" />
      <Badge label="PII" value={piiEnabled ? 'enabled' : 'disabled'} color="text-accent-cyan" />
      <Badge label="Audit" value={auditOn ? 'on' : 'off'} color="text-accent-blue" />
    </div>
  )
}
