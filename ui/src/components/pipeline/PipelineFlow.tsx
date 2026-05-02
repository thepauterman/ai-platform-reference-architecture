import { Monitor, Settings, Shield, GitBranch, Cloud, ChevronRight } from 'lucide-react'
import PipelineStep from './PipelineStep'
import type { PipelineStep as PipelineStepData } from '../../api/types'

interface Props {
  steps?: PipelineStepData[]
  activeStage?: number // -1 = all initializing, 0-4 = animating, 5+ = use steps data
}

const PIPELINE_STAGES = [
  { icon: <Monitor className="w-7 h-7" />, title: 'Client Application', subtitle: 'Web UI · API Consumer', defaultStatus: 'ACTIVE', color: 'green' as const },
  { icon: <Settings className="w-7 h-7" />, title: 'Gateway API', subtitle: 'FastAPI · /query · /health', defaultStatus: 'DONE', color: 'green' as const },
  { icon: <Shield className="w-7 h-7" />, title: 'Governance Layer', subtitle: 'PII Detection · Policy Engine', defaultStatus: 'PASS', color: 'green' as const },
  { icon: <GitBranch className="w-7 h-7" />, title: 'Routing Layer', subtitle: 'Classification · Provider Selection', defaultStatus: 'DONE', color: 'green' as const },
  { icon: <Cloud className="w-7 h-7" />, title: 'Model Providers', subtitle: 'gpt-4o · Claude 3.5 · Vertex AI', defaultStatus: 'READY', color: 'green' as const },
]

const stepMap: Record<number, string[]> = {
  0: ['CLIENT_REQUEST'],
  1: ['INPUT_VALIDATION'],
  2: ['SAFETY_CHECK', 'PII_DETECTION', 'POLICY_CHECK'],
  3: ['ROUTING_DECISION'],
  4: ['MODEL_INFERENCE', 'RESPONSE_STREAM'],
}

function resolveFromTrace(stageIndex: number, steps: PipelineStepData[]): { status: string; color: 'green' | 'yellow' | 'orange' | 'red'; active: boolean } {
  const relevantSteps = steps.filter(s => stepMap[stageIndex]?.includes(s.step))
  if (relevantSteps.length === 0) {
    return { status: 'PENDING', color: 'yellow', active: false }
  }

  const lastStep = relevantSteps[relevantSteps.length - 1]
  if (lastStep.status === 'FAIL' || lastStep.status === 'BLOCKED' || lastStep.status === 'ERROR') {
    return { status: lastStep.status, color: 'red', active: true }
  }

  const allDone = relevantSteps.every(s => ['OK', 'PASS', '200 OK', 'FALLBACK'].includes(s.status))
  if (allDone) {
    return { status: stageIndex === 2 ? 'PASS' : 'DONE', color: 'green', active: true }
  }

  return { status: 'RUNNING', color: 'orange', active: true }
}

function resolveStageStatus(
  stageIndex: number,
  steps: PipelineStepData[] | undefined,
  activeStage: number,
): { status: string; color: 'green' | 'yellow' | 'orange' | 'red'; active: boolean } {
  // If we have real trace data and animation is complete, use real data
  if (activeStage >= 5 && steps && steps.length > 0) {
    return resolveFromTrace(stageIndex, steps)
  }

  // Animation mode: -1 = all initializing, 0-4 = sequential highlight
  if (activeStage >= 0 && activeStage <= 4) {
    if (stageIndex < activeStage) {
      // Already passed — show done
      return { status: 'DONE', color: 'green', active: true }
    }
    if (stageIndex === activeStage) {
      // Currently active — show running
      return { status: 'RUNNING', color: 'orange', active: true }
    }
    // Not yet reached
    return { status: 'WAITING', color: 'yellow', active: false }
  }

  if (activeStage === -1) {
    // All initializing
    return { status: 'INIT', color: 'yellow', active: false }
  }

  // Default: show defaults (no query in progress)
  if (!steps || steps.length === 0) {
    return { status: PIPELINE_STAGES[stageIndex].defaultStatus, color: PIPELINE_STAGES[stageIndex].color, active: true }
  }

  return resolveFromTrace(stageIndex, steps)
}

export default function PipelineFlow({ steps, activeStage = 6 }: Props) {
  const completedCount = PIPELINE_STAGES.filter((_, i) => {
    const resolved = resolveStageStatus(i, steps, activeStage)
    return resolved.color === 'green'
  }).length

  // Count total steps: completed + 1 if something is running
  const hasRunning = PIPELINE_STAGES.some((_, i) => {
    const resolved = resolveStageStatus(i, steps, activeStage)
    return resolved.status === 'RUNNING'
  })
  const progressCount = completedCount + (hasRunning ? 1 : 0)

  return (
    <div className="px-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm text-muted uppercase tracking-widest">
          <span className="text-white font-medium">Architecture</span>
          <span>·</span>
          <span>Request Flow</span>
        </div>
        <div className="flex items-center gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <span
              key={i}
              className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
                i < completedCount
                  ? 'bg-accent-green'
                  : i < progressCount
                    ? 'bg-accent-orange animate-pulse'
                    : 'bg-muted/30'
              }`}
            />
          ))}
          <span className="text-sm text-muted ml-1">{progressCount}/6</span>
        </div>
      </div>

      <div className="flex items-stretch gap-0">
        {PIPELINE_STAGES.map((stage, i) => {
          const resolved = resolveStageStatus(i, steps, activeStage)
          return (
            <div key={stage.title} className="flex items-stretch flex-1">
              <PipelineStep
                icon={stage.icon}
                title={stage.title}
                subtitle={stage.subtitle}
                status={resolved.status}
                statusColor={resolved.color}
                active={resolved.active}
              />
              {i < PIPELINE_STAGES.length - 1 && (
                <div className="flex items-center px-1">
                  <ChevronRight className="w-4 h-4 text-muted/40" />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
