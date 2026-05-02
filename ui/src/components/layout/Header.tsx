import { Activity } from 'lucide-react'

export default function Header() {
  return (
    <header className="flex items-center gap-4 px-8 py-5">
      <div className="flex items-center justify-center w-11 h-11 rounded-full border border-card-border">
        <Activity className="w-6 h-6 text-accent-green" />
      </div>
      <h1 className="text-xl font-semibold tracking-wide text-white uppercase">
        AI Gateway Control Plane
      </h1>
    </header>
  )
}
