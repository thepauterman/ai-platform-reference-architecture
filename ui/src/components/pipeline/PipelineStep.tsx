import type { ReactNode } from 'react'

interface Props {
  icon: ReactNode
  title: string
  subtitle: string
  status: string
  statusColor: 'green' | 'yellow' | 'orange' | 'red' | 'blue'
  active?: boolean
}

const colors = {
  green: 'bg-accent-green/20 text-accent-green',
  yellow: 'bg-accent-yellow/20 text-accent-yellow',
  orange: 'bg-accent-orange/20 text-accent-orange',
  red: 'bg-accent-red/20 text-accent-red',
  blue: 'bg-accent-blue/20 text-accent-blue',
}

const dotColors = {
  green: 'bg-accent-green',
  yellow: 'bg-accent-yellow',
  orange: 'bg-accent-orange',
  red: 'bg-accent-red',
  blue: 'bg-accent-blue',
}

export default function PipelineStep({ icon, title, subtitle, status, statusColor, active = false }: Props) {
  const isRunning = status === 'RUNNING'

  return (
    <div
      className={`
        flex-1 rounded-lg border p-6 transition-all duration-500
        ${active
          ? isRunning
            ? 'border-accent-orange/40 bg-card shadow-[0_0_15px_rgba(249,115,22,0.08)]'
            : 'border-card-border bg-card'
          : 'border-card-border/30 bg-card/30 opacity-40'
        }
      `}
    >
      <div className="text-muted mb-4">{icon}</div>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
          isRunning ? `${dotColors[statusColor]} animate-pulse` : dotColors[statusColor]
        }`} />
        <span className={`text-base font-medium uppercase tracking-wider transition-colors duration-300 ${colors[statusColor]}`}>
          {status}
        </span>
      </div>
      <div className="text-xl font-medium text-white">{title}</div>
      <div className="text-base text-muted mt-1.5">{subtitle}</div>
    </div>
  )
}
