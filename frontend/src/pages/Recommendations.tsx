import { BookOpen, Sparkles } from 'lucide-react'

import { Button, Card, EmptyState, ErrorNote, PageHeader, Skeleton } from '../components/common'
import { MockNotice } from '../components/common/MockNotice'
import { CourseCard } from '../components/recommendation/CourseCard'
import { useGenerateRecommendations, useRecommendations } from '../hooks'
import { errorMessage } from '../lib/api'

export default function Recommendations() {
  const { data, isLoading } = useRecommendations()
  const generate = useGenerateRecommendations()

  const batch = generate.data ?? data
  const items = batch?.recommendations ?? []

  return (
    <>
      <PageHeader
        title="Recommendations"
        description="Semantic retrieval over the catalogue, ranked by a deterministic formula, explained by a language model."
        action={
          <Button
            variant="primary"
            icon={Sparkles}
            loading={generate.isPending}
            onClick={() => generate.mutate()}
          >
            {items.length > 0 ? 'Regenerate' : 'Get recommendations'}
          </Button>
        }
      />

      <div className="mb-4">
        <MockNotice />
      </div>

      {generate.isError && <ErrorNote>{errorMessage(generate.error)}</ErrorNote>}

      {batch && items.length > 0 && (
        <p className="mb-4 font-mono text-11 text-ink-3">
          batch={batch.batch_id.slice(0, 8)} · {batch.count} ranked ·{' '}
          {batch.ai_explanations} of {batch.count} explanations written by the model ·
          {batch.llm_available ? ' model configured' : ' model unavailable, templates in use'}
        </p>
      )}

      {(isLoading || generate.isPending) && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <Card key={index}>
              <Skeleton className="mb-3 h-5 w-2/3" />
              <Skeleton className="mb-2 h-4 w-1/3" />
              <Skeleton className="h-16 w-full" />
            </Card>
          ))}
        </div>
      )}

      {!isLoading && !generate.isPending && items.length === 0 && (
        <EmptyState
          icon={BookOpen}
          title="No recommendations yet. Generate a batch against your current skill gaps."
          action={
            <Button variant="primary" icon={Sparkles} onClick={() => generate.mutate()}>
              Get recommendations
            </Button>
          }
        />
      )}

      <div className="space-y-4">
        {items.map((item) => (
          <CourseCard key={item.id} item={item} />
        ))}
      </div>

      {items.length > 0 && (
        <p className="mt-6 max-w-prose text-12 leading-relaxed text-ink-3">
          Ranking is arithmetic: 0.35 × gap priority + 0.30 × semantic similarity + 0.20 × level fit
          + 0.10 × prerequisites met + 0.05 × format fit. Level fit targets your current level plus
          one, so the list recommends the next rung rather than the top of the ladder. The language
          model writes only the explanatory sentence, and when it is unavailable a template is used
          and labelled as such.
        </p>
      )}
    </>
  )
}
