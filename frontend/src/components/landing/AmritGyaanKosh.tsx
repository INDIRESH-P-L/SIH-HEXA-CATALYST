import { useState } from 'react'
import { ChevronLeft, ChevronRight, Clock, Sparkles, X } from 'lucide-react'

interface CaseStudy {
  id: string
  title: string
  category: string
  author: string
  readTime: string
  summary: string
  outcomes: string[]
  bgGradient: string
  tagColor: string
}

const CASE_STUDIES: CaseStudy[] = [
  {
    id: 'cs1',
    title: 'Scaling AI-Assisted Microdata Quality & Survey Analytics across MoSPI Field Offices',
    category: 'Statistical Systems & Analytics',
    author: 'By Capacity Building Commission & MoSPI DIID',
    readTime: '15 min read',
    summary: 'How deploying automated anomaly detection rules and deterministic skill-gap interventions across 2,400 field officers reduced non-sampling error rates in the Annual Survey of Unincorporated Enterprises (ASUE).',
    outcomes: [
      '38% faster data validation turnaround',
      'Targeted SQL & sampling interventions for 1,800+ field supervisors',
      '100% adherence to National Data Quality Framework guidelines',
    ],
    bgGradient: 'from-amber-700 via-orange-900 to-slate-900',
    tagColor: 'bg-amber-100 text-amber-900',
  },
  {
    id: 'cs2',
    title: 'Forest Landscapes & Socio-Economic Livelihood Assessment Indicators',
    category: 'Environment & Agriculture',
    author: 'By Capacity Building Commission',
    readTime: '20 min read',
    summary: 'Evaluating environmental satellite indices alongside household sampling frames to quantify tribal livelihood improvements under agroforestry interventions in Odisha and Chhattisgarh.',
    outcomes: [
      'Multi-source data fusion using QGIS and geospatial statistical packages',
      'Harmonized environmental indicators into state statistical abstracts',
    ],
    bgGradient: 'from-emerald-800 via-teal-950 to-slate-900',
    tagColor: 'bg-emerald-100 text-emerald-900',
  },
  {
    id: 'cs3',
    title: 'eHRMS-FRAC Integration: Precision Cadre Competency Mapping in NSSO',
    category: 'Digital Governance & Innovation',
    author: 'By Capacity Building Commission & DoPT',
    readTime: '25 min read',
    summary: 'Transitioning 4,500+ Statistical Officers from generic service records to role-based FRAC competencies, synchronizing assessment evidence directly with SPARROW annual performance appraisals.',
    outcomes: [
      'Automated skill-gap priority scoring replacing manual training nominations',
      'Decay modeling ensuring recency in technical software proficiencies',
    ],
    bgGradient: 'from-blue-800 via-indigo-950 to-slate-900',
    tagColor: 'bg-blue-100 text-blue-900',
  },
  {
    id: 'cs4',
    title: 'Waste to Wealth & Urban Local Body Efficiency: Data-Driven Municipal Governance',
    category: 'Governance & Public Administration',
    author: 'By Capacity Building Commission',
    readTime: '30 min read',
    summary: 'Empowering municipal sanitization officers with GIS routing, resource-tracking dashboards, and safety compliance training across 12 tier-2 cities.',
    outcomes: [
      '94% worker participation on iGOT mobile training app',
      'Measurable reduction in occupational hazards and turnaround lag',
    ],
    bgGradient: 'from-purple-900 via-slate-900 to-stone-900',
    tagColor: 'bg-purple-100 text-purple-900',
  },
]

export function AmritGyaanKosh({ onOpenLogin }: { onOpenLogin: () => void }) {
  const [selectedCase, setSelectedCase] = useState<CaseStudy | null>(null)
  const [startIndex, setStartIndex] = useState(0)

  const itemsVisible = 4
  const maxStart = Math.max(0, CASE_STUDIES.length - itemsVisible)

  function nextSlide() {
    setStartIndex((prev) => (prev + 1 > maxStart ? 0 : prev + 1))
  }

  function prevSlide() {
    setStartIndex((prev) => (prev - 1 < 0 ? maxStart : prev - 1))
  }

  const visibleStudies = CASE_STUDIES.slice(startIndex, startIndex + itemsVisible)

  return (
    <section id="case-studies" className="karmayogi-pattern py-12 px-4 sm:px-6 lg:px-8 border-b border-amber-200/60">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header with Title and View All */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-[#F58220]" />
              <h2 className="text-24 sm:text-28 font-extrabold text-[#0B3060]">
                Amrit Gyaan Kosh Case Studies
              </h2>
            </div>
            <p className="text-13 text-slate-600">
              Transformational governance blueprints, statistical innovations, and frontline impact stories
            </p>
          </div>
          <button
            type="button"
            onClick={onOpenLogin}
            className="text-13 font-bold text-[#D96B0B] hover:text-[#0B3060] transition-colors"
          >
            Show all →
          </button>
        </div>

        {/* Carousel Container */}
        <div className="relative">
          {/* Left Arrow */}
          <button
            type="button"
            onClick={prevSlide}
            aria-label="Previous case studies"
            className="absolute -left-3 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/80 text-white shadow-lg hover:bg-black transition-all"
          >
            <ChevronLeft size={22} />
          </button>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {visibleStudies.map((study) => (
              <div
                key={study.id}
                onClick={() => setSelectedCase(study)}
                className="group cursor-pointer overflow-hidden rounded-xl border border-amber-200/90 bg-white shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Card Thumbnail Graphic */}
                  <div className={`relative h-40 w-full bg-gradient-to-br ${study.bgGradient} p-4 flex flex-col justify-between text-white`}>
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-black/40 backdrop-blur px-2 py-0.5 text-10 font-bold uppercase tracking-wider text-amber-200">
                        Case Study
                      </span>
                      <span className="flex items-center gap-1 text-11 text-amber-200 font-bold bg-black/40 px-2 py-0.5 rounded">
                        <Clock size={12} /> {study.readTime}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded bg-white/20 text-white font-bold text-12">
                        📄
                      </div>
                      <span className="text-11 font-mono text-amber-200 font-bold">
                        AMRIT GYAAN KOSH
                      </span>
                    </div>
                  </div>

                  {/* Card Details */}
                  <div className="p-4 space-y-2">
                    <span className={`inline-block rounded px-2 py-0.5 text-10 font-bold ${study.tagColor}`}>
                      {study.category}
                    </span>

                    <h3 className="text-13 font-bold text-slate-900 leading-snug line-clamp-3 group-hover:text-[#F58220] transition-colors">
                      {study.title}
                    </h3>

                    <p className="text-11 text-slate-500 font-medium truncate pt-1">
                      {study.author}
                    </p>
                  </div>
                </div>

                <div className="p-4 pt-0">
                  <span className="inline-flex items-center gap-1 text-12 font-bold text-[#0B3060] group-hover:text-[#F58220]">
                    Read Full Case Study →
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Right Arrow */}
          <button
            type="button"
            onClick={nextSlide}
            aria-label="Next case studies"
            className="absolute -right-3 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/80 text-white shadow-lg hover:bg-black transition-all"
          >
            <ChevronRight size={22} />
          </button>
        </div>

        {/* Selected Case Study Modal */}
        {selectedCase && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
            <div className="relative w-full max-w-2xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl max-h-[90vh] flex flex-col">
              <div className="tricolor-strip" />
              <div className="flex items-center justify-between border-b border-slate-100 bg-[#FFF7ED] px-6 py-4">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-[#0B3060] px-2.5 py-0.5 text-11 font-bold text-white">
                    Amrit Gyaan Kosh
                  </span>
                  <span className="text-12 font-semibold text-slate-600">{selectedCase.category}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedCase(null)}
                  className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-6 space-y-4 overflow-y-auto">
                <h3 className="text-20 font-extrabold text-[#0B3060] leading-snug">
                  {selectedCase.title}
                </h3>
                <div className="flex items-center gap-3 text-12 text-slate-500 font-medium pb-2 border-b border-slate-100">
                  <span>{selectedCase.author}</span>
                  <span>•</span>
                  <span>⏱️ {selectedCase.readTime}</span>
                </div>

                <div className="space-y-3 text-14 text-slate-700 leading-relaxed">
                  <p className="font-semibold text-slate-900">Executive Summary:</p>
                  <p>{selectedCase.summary}</p>
                </div>

                <div className="rounded-lg bg-emerald-50/80 p-4 border border-emerald-200 space-y-2">
                  <span className="text-12 font-bold uppercase tracking-wider text-emerald-900 block">
                    Key Implementation Outcomes
                  </span>
                  <ul className="space-y-1.5 text-13 text-emerald-950">
                    {selectedCase.outcomes.map((o, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-emerald-700 font-bold">✓</span>
                        <span>{o}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedCase(null)
                      onOpenLogin()
                    }}
                    className="w-full rounded-lg bg-[#0B3060] py-2.5 text-14 font-bold text-white shadow hover:bg-[#F58220] transition-colors text-center"
                  >
                    Log In to Access Full Document Repository
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
