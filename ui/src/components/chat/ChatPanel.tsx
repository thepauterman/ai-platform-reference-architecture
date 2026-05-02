import { useState, useRef, useEffect } from 'react'
import { ArrowRight } from 'lucide-react'
import { queryGateway } from '../../api/client'
import type { QueryResponse } from '../../api/types'
import ModelBadges from './ModelBadges'

interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: QueryResponse
}

interface Props {
  onQueryStart?: () => void
  onQueryComplete?: (requestId: string | null) => void
}

export default function ChatPanel({ onQueryStart, onQueryComplete }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastModel, setLastModel] = useState('gpt-4o')
  const [lastRouting, setLastRouting] = useState('auto-route')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  // Auto-focus input on mount and after each query
  useEffect(() => {
    inputRef.current?.focus()
  }, [loading])

  const handleSubmit = async () => {
    const prompt = input.trim()
    if (!prompt || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: prompt }])
    setLoading(true)
    onQueryStart?.()

    try {
      const res = await queryGateway({ prompt })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response || 'No response',
        meta: res,
      }])
      if (res.model_used) setLastModel(res.model_used)
      if (res.classification) setLastRouting(res.classification)
      onQueryComplete?.(res.request_id)
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${e instanceof Error ? e.message : 'Request failed'}`,
      }])
      onQueryComplete?.(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full border-l border-card-border bg-card">
      <div className="px-6 py-5 border-b border-card-border">
        <h2 className="text-lg font-semibold text-white uppercase tracking-wider">AI Gateway Prompt</h2>
      </div>

      <ModelBadges model={lastModel} routing={lastRouting} />

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div className="flex justify-end">
                <div className="bg-card-border/60 rounded-lg px-5 py-3 max-w-[90%] text-xl text-white">
                  {msg.content}
                </div>
              </div>
            ) : (
              <div>
                <div className="text-xl text-gray-300 leading-relaxed whitespace-pre-wrap [&>p]:mb-3">
                  {msg.content.split('\n\n').map((para, j) => (
                    <p key={j}>{para}</p>
                  ))}
                </div>
                {msg.meta && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {msg.meta.model_used && (
                      <span className="px-3 py-1 rounded-full text-sm border border-card-border text-muted">
                        {msg.meta.model_used}
                      </span>
                    )}
                    {msg.meta.request_id && (
                      <span className="px-3 py-1 rounded-full text-sm border border-card-border text-muted">
                        {msg.meta.classification}
                      </span>
                    )}
                    <span className={`px-3 py-1 rounded-full text-sm border ${
                      msg.meta.policy_checked
                        ? 'border-accent-green/30 text-accent-green'
                        : 'border-accent-red/30 text-accent-red'
                    }`}>
                      {msg.meta.policy_checked ? 'PASS' : 'FAIL'}
                    </span>
                    {msg.meta.fallback_used && (
                      <span className="px-3 py-1 rounded-full text-sm border border-accent-yellow/30 text-accent-yellow">
                        fallback
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="text-base text-muted animate-pulse">Processing through gateway...</div>
        )}
      </div>

      <div className="p-5 border-t border-card-border">
        <div className="flex items-center gap-3 bg-surface rounded-lg border border-card-border px-5 py-4">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Ask AI Gateway..."
            className="flex-1 bg-transparent text-xl text-white placeholder-muted focus:outline-none"
            disabled={loading}
            autoFocus
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="w-11 h-11 flex items-center justify-center rounded-full bg-card-border/60 hover:bg-card-border transition-colors disabled:opacity-30"
          >
            <ArrowRight className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
