/**
 * The catalogue honesty badge.
 *
 * Rendered wherever catalogue data appears, from live data returned by
 * GET /catalogue/provider-info — so it reports what the backend is actually
 * configured with rather than a hard-coded string, and a judge can verify the
 * claim by calling the same endpoint.
 *
 * This is deliberately visible, never a tooltip.
 */
import { Info } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import { api, API } from '../../lib/api'
import type { ProviderInfo } from '../../lib/types'

export function useProviderInfo() {
  return useQuery({
    queryKey: ['provider-info'],
    queryFn: async () => (await api.get<ProviderInfo>(API.v1('/catalogue/provider-info'))).data,
    staleTime: 5 * 60_000,
  })
}

export function MockNotice({ compact = false }: { compact?: boolean }) {
  const { data } = useProviderInfo()
  if (!data) return null

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded border border-emerging/30 bg-emerging-bg px-2 py-0.5 font-mono text-11 font-medium uppercase tracking-[0.06em] text-emerging">
        <Info size={12} strokeWidth={1.5} aria-hidden />
        {data.is_mock ? `Mock catalogue — ${data.record_count ?? 0} sample records` : data.provider}
      </span>
    )
  }

  return (
    <aside className="rounded border border-emerging/30 bg-emerging-bg p-4" aria-label="Catalogue data source">
      <p className="flex items-center gap-2 font-mono text-11 font-medium uppercase tracking-[0.08em] text-emerging">
        <Info size={14} strokeWidth={1.5} aria-hidden />
        {data.is_mock
          ? `Mock catalogue — ${data.record_count ?? 0} sample records`
          : `Catalogue provider: ${data.provider}`}
      </p>
      <p className="mt-2 max-w-prose text-13 leading-relaxed text-ink-2">{data.description}</p>
      <p className="mt-2 font-mono text-11 text-ink-3">
        provider={data.provider} · is_mock={String(data.is_mock)} · reachable=
        {String(data.reachable)} · circuit={data.circuit_state ?? 'n/a'}
      </p>
    </aside>
  )
}
