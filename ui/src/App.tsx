import { useState, useCallback, useRef } from 'react'
import Header from './components/layout/Header'
import PipelineFlow from './components/pipeline/PipelineFlow'
import ObservabilityBar from './components/observability/ObservabilityBar'
import AuditLog from './components/audit/AuditLog'
import MetricsGrid from './components/metrics/MetricsGrid'
import ChatPanel from './components/chat/ChatPanel'
import type { PipelineStep } from './api/types'

export default function App() {
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([])
  const [activeStage, setActiveStage] = useState<number>(-1)
  const [queryVersion, setQueryVersion] = useState(0)
  const animationTimers = useRef<ReturnType<typeof setTimeout>[]>([])

  const clearTimers = useCallback(() => {
    animationTimers.current.forEach(t => clearTimeout(t))
    animationTimers.current = []
  }, [])

  const handleQueryStart = useCallback(() => {
    clearTimers()
    // Reset everything to initializing
    setPipelineSteps([])
    setActiveStage(-1) // -1 = all initializing

    // Animate through stages sequentially
    const delays = [200, 600, 1200, 2000, 3500]
    delays.forEach((delay, i) => {
      const t = setTimeout(() => setActiveStage(i), delay)
      animationTimers.current.push(t)
    })
  }, [clearTimers])

  const handleQueryComplete = useCallback((requestId: string | null) => {
    clearTimers()
    setActiveStage(5) // all complete
    setQueryVersion(v => v + 1)

    // The audit log will pick up the new request via the version bump
    // and load the trace, which updates pipelineSteps with real data
    if (requestId) {
      // Small delay to let the audit log write complete on the backend
      const t = setTimeout(() => {
        setQueryVersion(v => v + 1)
      }, 500)
      animationTimers.current.push(t)
    }
  }, [clearTimers])

  return (
    <div className="h-screen grid grid-cols-[1fr_800px]">
      <main className="overflow-y-auto">
        <Header />
        <PipelineFlow steps={pipelineSteps} activeStage={activeStage} />
        <ObservabilityBar />
        <AuditLog
          onTraceLoaded={setPipelineSteps}
          queryVersion={queryVersion}
        />
        <MetricsGrid queryVersion={queryVersion} />

        <footer className="mx-8 mt-10 mb-6 pt-6 border-t border-card-border/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-muted tracking-wide uppercase">marscouncil</span>
            <span className="text-muted/40">|</span>
            <span className="text-sm text-muted/60">AI Governance Gateway</span>
          </div>
          <div className="text-sm text-muted/40">
            v0.1.0
          </div>
        </footer>
      </main>

      <aside className="h-screen">
        <ChatPanel
          onQueryStart={handleQueryStart}
          onQueryComplete={handleQueryComplete}
        />
      </aside>
    </div>
  )
}
