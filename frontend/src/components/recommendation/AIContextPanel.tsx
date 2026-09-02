/**
 * The exact anonymised JSON that was sent to the language model.
 *
 * Stored at generation time rather than reconstructed for display, so what is
 * shown here is what actually left the process. Twenty minutes of work and the
 * most persuasive thing in the demonstration.
 */
import { useRecommendationContext } from '../../hooks'
import { Spinner } from '../common'

export function AIContextPanel({ recommendationId }: { recommendationId: string }) {
  const { data, isLoading, isError } = useRecommendationContext(recommendationId)

  return (
    <details className="rounded border border-rule bg-surface-2">
      <summary className="cursor-pointer list-none px-3 py-2 text-13 font-medium text-ink marker:hidden">
        <span className="select-none">Context sent to the model — no personal data</span>
      </summary>
      <div className="border-t border-rule px-3 py-3">
        {isLoading && <Spinner label="Loading the payload" />}
        {isError && (
          <p className="text-13 text-ink-2">The stored context could not be loaded.</p>
        )}
        {data && (
          <>
            <pre className="max-h-80 overflow-auto rounded border border-rule bg-surface p-3 font-mono text-12 leading-relaxed text-ink">
              {JSON.stringify(data.ai_context_sent, null, 2)}
            </pre>
            <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-2">{data.context_note}</p>
            {data.model && (
              <p className="mt-1 font-mono text-11 text-ink-3">model={data.model}</p>
            )}
          </>
        )}
      </div>
    </details>
  )
}
