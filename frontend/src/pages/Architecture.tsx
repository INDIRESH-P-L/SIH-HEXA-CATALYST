/**
 * The system architecture, rendered from the same facts the platform runs on.
 *
 * Not a static diagram: the counts come from live endpoints, so what is shown
 * is what is actually deployed.
 */
import { useQuery } from '@tanstack/react-query'
import {
  Boxes,
  CircleDot,
  Database,
  GitBranch,
  Layers,
  ShieldCheck,
  Sparkles,
  Users,
} from 'lucide-react'

import { Badge, Card, PageHeader, Skeleton } from '../components/common'
import { useProviderInfo } from '../components/common/MockNotice'
import { useCompetencies, useHealth } from '../hooks'
import { api, API } from '../lib/api'
import type { CorpusStats } from '../lib/types'

type Kind = 'deterministic' | 'vector' | 'llm' | 'human' | 'external' | 'datastore'

const KIND_STYLE: Record<Kind, string> = {
  deterministic: 'border-rule bg-surface text-ink',
  vector: 'border-layer-measure/40 bg-layer-measure/[0.06] text-ink',
  llm: 'border-layer-decide/40 bg-layer-decide/[0.06] text-ink',
  human: 'border-emerging/40 bg-emerging-bg text-ink',
  external: 'border-dashed border-ink-3/50 bg-surface-2 text-ink-2',
  datastore: 'border-accent-line bg-accent-wash text-ink',
}

const KIND_LABEL: Record<Kind, string> = {
  deterministic: 'Deterministic service',
  vector: 'Vector / semantic',
  llm: 'LLM-backed step',
  human: 'Human decision gate',
  external: 'External system',
  datastore: 'Datastore',
}

interface ModuleSpec {
  id: string
  name: string
  kind: Kind
  summary: string
  detail: string[]
}

interface LayerSpec {
  key: string
  title: string
  subtitle: string
  accent: string
  modules: ModuleSpec[]
}

const LAYERS: LayerSpec[] = [
  {
    key: 'sources',
    title: 'Sources',
    subtitle: 'Everything the platform consumes but does not own',
    accent: 'text-layer-source',
    modules: [
      {
        id: 'SSO',
        name: 'Parichay / iGOT SSO',
        kind: 'external',
        summary: 'OIDC identity',
        detail: ['Architecture only — no government SSO is integrated.'],
      },
      {
        id: 'IGOT',
        name: 'iGOT Karmayogi',
        kind: 'external',
        summary: 'Course catalogue and progress',
        detail: ['Mocked behind a documented interface. Production needs authorised credentials.'],
      },
      {
        id: 'NSSTA',
        name: 'NSSTA / TPAC',
        kind: 'external',
        summary: 'Approved training calendar',
        detail: ['Dated, seat-limited programmes. Nominated for, not enrolled in.'],
      },
      {
        id: 'UPLOAD',
        name: 'Uploaded material',
        kind: 'external',
        summary: 'PDF · PPTX · DOCX',
        detail: ['What the assessment generator and the assistant read from.'],
      },
    ],
  },
  {
    key: 'foundation',
    title: 'Foundation',
    subtitle: 'Who the officer is, and what the job expects',
    accent: 'text-layer-foundation',
    modules: [
      {
        id: 'M1',
        name: 'Identity & Profile',
        kind: 'deterministic',
        summary: 'Composed profile with provenance',
        detail: [
          'Four sources routinely disagree about a designation. Each claim is stored with its source, confidence and effective date, so the resolver can choose and an administrator can correct.',
          'Position → Role is the most load-bearing field in the platform: every expected level, dashboard scope and nomination authority derives from it.',
          'Correction is appended as a new row. Nothing is overwritten.',
        ],
      },
      {
        id: 'M2',
        name: 'Competency Framework',
        kind: 'vector',
        summary: 'FRAC graph, versioned, embedded',
        detail: [
          'Position → Role → Activity → Competency, mirroring the model iGOT already uses.',
          'A sealed framework version is immutable. Without it a dashboard from last quarter silently rewrites itself and training effectiveness becomes impossible to measure.',
          'Decay classes mark how fast evidence goes stale: tools 18 months, regulatory 12, methodology 36, behavioural never.',
        ],
      },
    ],
  },
  {
    key: 'measure',
    title: 'Measure',
    subtitle: 'Turning performance into evidence',
    accent: 'text-layer-measure',
    modules: [
      {
        id: 'M3',
        name: 'Assessment Engine',
        kind: 'deterministic',
        summary: 'Adaptive delivery, deterministic scoring',
        detail: [
          'Difficulty-weighted: 100 × Σ(w·c) / Σ(w), over items attempted, with weights easy 1, medium 2, hard 3.',
          'Bands map onto FRAC through SME cut-scores set per competency, never one global threshold.',
          'The scorer is a pure function of responses, item metadata and cut-scores. Re-running it must reproduce the number exactly — that is the audit test.',
        ],
      },
      {
        id: 'M8',
        name: 'AI Assessment Generator',
        kind: 'llm',
        summary: 'Uploaded material → verified items',
        detail: [
          'Generation is the easy half. An unverified question bank fails predictably: two defensible answers, a giveaway distractor, a stem answerable without the source.',
          'Ten deterministic checks decide what survives. No model votes on question quality.',
          'Every published item carries the source span it was generated from, so a reviewer can always see where a question came from.',
        ],
      },
    ],
  },
  {
    key: 'decide',
    title: 'Decide',
    subtitle: 'From evidence to a defensible next step',
    accent: 'text-layer-decide',
    modules: [
      {
        id: 'M4',
        name: 'Skill Gap Engine',
        kind: 'deterministic',
        summary: 'Expected − current, weighted',
        detail: [
          'priority = (expected − current) × criticality × (2 − confidence) × horizon.',
          'The (2 − confidence) term is the one that matters: an unmeasured competency sits near 0.25 confidence, which nearly doubles its priority. "We do not know whether this officer can do this" is surfaced as urgent, which is the honest position.',
          'Every result snapshots per officer, framework version and date, so a past dashboard recomputes identically.',
        ],
      },
      {
        id: 'M5',
        name: 'Recommendation Engine',
        kind: 'vector',
        summary: 'Retrieve → rank → sequence',
        detail: [
          'Dense, lexical and tag retrieval fused by reciprocal rank, then seven weighted terms, then sequencing against a prerequisite graph and a calendar.',
          'Collapsing these into one similarity search is the common mistake: it produces recommendations that are topically plausible and operationally useless.',
          'Cold start, honestly: there is no collaborative signal on day one. The seam exists and stays empty until M9 has real outcome data.',
        ],
      },
      {
        id: 'M6',
        name: 'iGOT / NSSTA Integration',
        kind: 'external',
        summary: 'Anti-corruption boundary',
        detail: [
          'No external schema passes this line. Two adapters, because the two catalogues behave nothing alike.',
          'A circuit breaker and a local mirror mean the platform keeps working when the API does not; writes queue in an outbox and are retried.',
          'One catalogue is enrolled into; the other requires a nomination a human approves.',
        ],
      },
      {
        id: 'M7',
        name: 'Learning & AI Assistant',
        kind: 'llm',
        summary: 'Grounded, cited, willing to refuse',
        detail: [
          'Answers from the organisation’s approved material, not from whatever the model remembers.',
          'The refusal branch is a feature. "This is not in the approved corpus, here is the course that covers it" is the correct behaviour when a confident wrong answer would be worse.',
        ],
      },
    ],
  },
  {
    key: 'observe',
    title: 'Observe',
    subtitle: 'Whether any of it worked',
    accent: 'text-layer-observe',
    modules: [
      {
        id: 'M9',
        name: 'Analytics & Competency Tracking',
        kind: 'deterministic',
        summary: 'Events → rollups → two dashboards',
        detail: [
          'One append-only event stream is what makes every downstream number reconcilable. Dashboards read marts, marts rebuild from events, and an event is never edited.',
          'Completion percentage answers "did they attend". Pre/post competency delta answers "did it work" — and that is the number needed to plan a training calendar.',
          'No aggregate is shown over fewer than five officers, and no individual score appears in any workforce view.',
        ],
      },
    ],
  },
]

function useCorpus() {
  return useQuery({
    queryKey: ['assistant', 'corpus'],
    queryFn: async () => (await api.get<CorpusStats>(API.v1('/assistant/corpus'))).data,
    staleTime: 60_000,
  })
}

function ModuleCard({ module }: { module: ModuleSpec }) {
  return (
    <details className={`rounded border p-4 ${KIND_STYLE[module.kind]}`}>
      <summary className="cursor-pointer list-none marker:hidden">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-mono text-11 uppercase tracking-[0.08em] text-ink-3">
              {module.id}
            </p>
            <h3 className="mt-0.5 text-14 font-semibold text-ink">{module.name}</h3>
            <p className="mt-0.5 text-12 text-ink-2">{module.summary}</p>
          </div>
          <CircleDot size={14} strokeWidth={1.5} className="mt-1 shrink-0 text-ink-3" aria-hidden />
        </div>
      </summary>
      <div className="mt-3 space-y-2 border-t border-rule-2 pt-3">
        {module.detail.map((line) => (
          <p key={line} className="max-w-prose text-12 leading-relaxed text-ink-2">
            {line}
          </p>
        ))}
        <p className="pt-1 font-mono text-11 text-ink-3">{KIND_LABEL[module.kind]}</p>
      </div>
    </details>
  )
}

export default function Architecture() {
  const health = useHealth()
  const provider = useProviderInfo()
  const competencies = useCompetencies()
  const corpus = useCorpus()

  return (
    <>
      <PageHeader
        title="System architecture"
        description="Nine modules across five layers. Deterministic core, AI at the edges — no language model ever produces or adjusts a competency score."
      />

      {/* Live facts, not a static diagram. */}
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <p className="eyebrow mb-2">Competency framework</p>
          {competencies.isLoading ? (
            <Skeleton className="h-8 w-16" />
          ) : (
            <p className="font-mono text-32 font-medium tabular text-ink">
              {competencies.data?.length ?? 0}
            </p>
          )}
          <p className="text-12 text-ink-3">competencies, four domains</p>
        </Card>
        <Card>
          <p className="eyebrow mb-2">Catalogue mirror</p>
          <p className="font-mono text-32 font-medium tabular text-ink">
            {provider.data?.record_count ?? 0}
          </p>
          <p className="text-12 text-ink-3">
            offerings, {provider.data?.embedded_count ?? 0} embedded
          </p>
        </Card>
        <Card>
          <p className="eyebrow mb-2">Approved corpus</p>
          <p className="font-mono text-32 font-medium tabular text-ink">
            {corpus.data?.indexed_chunks ?? 0}
          </p>
          <p className="text-12 text-ink-3">
            chunks from {corpus.data?.approved_materials ?? 0} documents
          </p>
        </Card>
        <Card>
          <p className="eyebrow mb-2">Embeddings</p>
          <p className="font-mono text-16 font-medium text-ink">bge-small-en-v1.5</p>
          <p className="mt-1 text-12 text-ink-3">
            384 dimensions, in-process, no network call
          </p>
        </Card>
      </div>

      {/* The five layers */}
      <div className="space-y-4">
        {LAYERS.map((layer) => (
          <Card key={layer.key}>
            <div className="mb-4 flex items-baseline justify-between gap-4">
              <div>
                <h2 className={`font-mono text-11 font-medium uppercase tracking-[0.08em] ${layer.accent}`}>
                  {layer.title}
                </h2>
                <p className="mt-1 text-13 text-ink-2">{layer.subtitle}</p>
              </div>
              <span className="font-mono text-11 text-ink-3">
                {layer.modules.length} {layer.modules.length === 1 ? 'component' : 'components'}
              </span>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
              {layer.modules.map((module) => (
                <ModuleCard key={module.id} module={module} />
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* The two datastores everything flows through */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card label="Evidence ledger">
          <div className="flex items-start gap-3">
            <Database size={20} strokeWidth={1.5} className="mt-0.5 shrink-0 text-accent" aria-hidden />
            <div>
              <p className="max-w-prose text-13 leading-relaxed text-ink-2">
                Append-only. Every competency change enters here tagged with source, confidence
                and framework version, so any number on screen can be derived on demand. No table
                stores a mutable “current level”; a level is the most recent row.
              </p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <Badge>self-declared 0.25</Badge>
                <Badge>practice 0.50</Badge>
                <Badge>iGOT completion 0.45</Badge>
                <Badge>NSSTA programme 0.80</Badge>
                <Badge>proctored assessment 0.90</Badge>
              </div>
            </div>
          </div>
        </Card>
        <Card label="Normalised catalogue">
          <div className="flex items-start gap-3">
            <Boxes size={20} strokeWidth={1.5} className="mt-0.5 shrink-0 text-accent" aria-hidden />
            <p className="max-w-prose text-13 leading-relaxed text-ink-2">
              iGOT and NSSTA offerings on one schema, embedded on ingest and held locally. That
              mirror is the offline guarantee: when the catalogue service is unreachable, the
              platform serves its own copy and queues writes rather than failing.
            </p>
          </div>
        </Card>
      </div>

      {/* The principle */}
      <Card className="mt-4" label="Where AI is used, and where it is not">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <p className="mb-2 flex items-center gap-2 text-13 font-semibold text-ink">
              <Sparkles size={16} strokeWidth={1.5} className="text-layer-decide" aria-hidden />
              The model writes
            </p>
            <ul className="space-y-1 text-13 text-ink-2">
              <li>· one explanatory sentence per recommendation</li>
              <li>· candidate question stems, options and rationales</li>
              <li>· the prose around a quiz result, after scoring</li>
              <li>· grounded answers over the approved corpus, with citations</li>
            </ul>
          </div>
          <div>
            <p className="mb-2 flex items-center gap-2 text-13 font-semibold text-ink">
              <ShieldCheck size={16} strokeWidth={1.5} className="text-met" aria-hidden />
              Deterministic code decides
            </p>
            <ul className="space-y-1 text-13 text-ink-2">
              <li>· the gap, its band and its priority</li>
              <li>· the ranking and sequencing of every recommendation</li>
              <li>· whether a generated question is usable — all ten checks</li>
              <li>· the score, the competency level, and every dashboard figure</li>
            </ul>
          </div>
        </div>
        <p className="mt-4 max-w-prose border-t border-rule-2 pt-3 text-12 leading-relaxed text-ink-3">
          A competency score feeds nomination and posting decisions and must be defensible by
          anyone holding the scoring rule. That is why nothing which produces a number is produced
          by a model.
        </p>
      </Card>

      {/* Legend */}
      <Card className="mt-4" label="Legend">
        <div className="flex flex-wrap gap-2">
          {(Object.keys(KIND_LABEL) as Kind[]).map((kind) => (
            <span
              key={kind}
              className={`inline-flex items-center rounded border px-2 py-1 text-12 ${KIND_STYLE[kind]}`}
            >
              {KIND_LABEL[kind]}
            </span>
          ))}
        </div>
      </Card>

      {/* Deployment reality */}
      <Card className="mt-4" label="What is deployed right now">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-13 md:grid-cols-4">
          <div>
            <dt className="flex items-center gap-1.5 text-ink-3">
              <Users size={14} strokeWidth={1.5} aria-hidden />
              Auth seam
            </dt>
            <dd className="mt-0.5 font-mono text-ink">{health.data?.auth_mode ?? '—'}</dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-ink-3">
              <Layers size={14} strokeWidth={1.5} aria-hidden />
              Storage seam
            </dt>
            <dd className="mt-0.5 font-mono text-ink">{health.data?.storage_mode ?? '—'}</dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-ink-3">
              <GitBranch size={14} strokeWidth={1.5} aria-hidden />
              Catalogue provider
            </dt>
            <dd className="mt-0.5 font-mono text-ink">
              {health.data?.catalogue_provider ?? '—'}
              {provider.data?.is_mock ? ' (mock)' : ''}
            </dd>
          </div>
          <div>
            <dt className="flex items-center gap-1.5 text-ink-3">
              <Sparkles size={14} strokeWidth={1.5} aria-hidden />
              Language model
            </dt>
            <dd className="mt-0.5 font-mono text-ink">{health.data?.llm.status ?? '—'}</dd>
          </div>
        </dl>
        <p className="mt-4 max-w-prose text-12 leading-relaxed text-ink-3">
          Each of these is a seam with two implementations selected by one environment variable.
          Token verification in particular is a single function, which is what “SSO-ready” means
          here — and no government single sign-on is integrated.
        </p>
      </Card>
    </>
  )
}
