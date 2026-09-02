/**
 * Marks text a language model wrote, and distinguishes it from the templated
 * fallback. Presenting a template as model output would be dishonest, so the
 * source travels with the text.
 */
import { Sparkles, FileText } from 'lucide-react'

export function AIBadge({ source }: { source: 'ai' | 'template' | string }) {
  const isAI = source === 'ai'
  const Icon = isAI ? Sparkles : FileText
  return (
    <span className="inline-flex items-center gap-1 font-mono text-11 font-medium uppercase tracking-[0.08em] text-ink-3">
      <Icon size={12} strokeWidth={1.5} aria-hidden />
      {isAI ? 'AI-generated' : 'Template (AI unavailable)'}
    </span>
  )
}
