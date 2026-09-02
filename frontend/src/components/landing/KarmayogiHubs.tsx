import { useState } from 'react'
import { Award, BookOpen, Briefcase, ChevronRight, GraduationCap, Network, Play, Sparkles, Target, BarChart3 } from 'lucide-react'

const HUBS = [
  {
    id: 'competency',
    name: 'Competency Hub',
    icon: Target,
    tagline: 'FRAC 4-Point Competency Profiler',
    description: 'Competency Hub reveals the recommended competencies for your position, discovering your growth opportunities, decay rates, and expected proficiency tiers.',
    color: 'bg-amber-500 text-white',
    ringColor: 'border-amber-400',
    stats: '33 Sealed Competencies across 4 Domains',
    position: 'top-0 left-1/2 -translate-x-1/2 -translate-y-4',
  },
  {
    id: 'learning',
    name: 'Learning Hub',
    icon: BookOpen,
    tagline: 'Semantic Recommendation Engine',
    description: 'Explore 6,400+ accredited courses across iGOT and NSSTA, ranked with reciprocal rank fusion (RRF) targeting your largest skill gaps.',
    color: 'bg-blue-600 text-white',
    ringColor: 'border-blue-400',
    stats: '41 Statistical & Governance Modules',
    position: 'top-1/4 right-0 translate-x-3',
  },
  {
    id: 'assessment',
    name: 'Assessment Hub',
    icon: GraduationCap,
    tagline: 'Deterministic Cut-Score Engine',
    description: 'Take proctored and diagnostic quizzes with difficulty-weighted scoring. Earning a cut-score updates your FRAC level immediately in one transaction.',
    color: 'bg-emerald-600 text-white',
    ringColor: 'border-emerald-400',
    stats: '10 Deterministic Validation Gates',
    position: 'bottom-1/4 right-0 translate-x-3',
  },
  {
    id: 'analytics',
    name: 'Analytics Hub',
    icon: BarChart3,
    tagline: 'Workforce Intelligence & Marts',
    description: 'Monitor cadre-wide capacity building, training effectiveness vs. comparison groups, and role-competency heatmaps protected by k-anonymity.',
    color: 'bg-purple-600 text-white',
    ringColor: 'border-purple-400',
    stats: 'Real-time Event Store & Rollup Marts',
    position: 'bottom-0 left-1/2 -translate-x-1/2 translate-y-4',
  },
  {
    id: 'career',
    name: 'Career Hub',
    icon: Briefcase,
    tagline: 'eHRMS & SPARROW Integration',
    description: 'Align your verified competency achievements with cadre transfer postings, deputation eligibility, and official annual appraisal records.',
    color: 'bg-indigo-600 text-white',
    ringColor: 'border-indigo-400',
    stats: 'Direct SPARROW APAR Provenance',
    position: 'bottom-1/4 left-0 -translate-x-3',
  },
  {
    id: 'network',
    name: 'Network Hub',
    icon: Network,
    tagline: 'Peer & SME Community',
    description: 'Connect with Subject Matter Experts across MoSPI, NSSTA faculty, and statistical officers nationwide for collaborative knowledge sharing.',
    color: 'bg-rose-600 text-white',
    ringColor: 'border-rose-400',
    stats: '43+ Lakh Active Officials',
    position: 'top-1/4 left-0 -translate-x-3',
  },
]

export function KarmayogiHubs({ onOpenLogin }: { onOpenLogin: () => void }) {
  const [selectedHub, setSelectedHub] = useState<(typeof HUBS)[number]>(HUBS[0]!)

  return (
    <section id="hubs" className="bg-white py-14 px-4 sm:px-6 lg:px-8 border-b border-slate-200">
      <div className="mx-auto max-w-7xl space-y-10">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 border border-amber-200 px-3 py-0.5 text-11 font-bold text-[#D96B0B] uppercase tracking-wider">
            <Sparkles size={13} />
            <span>Integrated Capacity Ecosystem</span>
          </div>
          <h2 className="text-26 sm:text-30 font-extrabold text-[#0B3060]">Karmayogi Hubs</h2>
          <p className="text-14 text-slate-600 max-w-2xl mx-auto">
            Six interconnected intelligence pillars empowering government officials from recruitment to continuous lifelong learning
          </p>
        </div>

        {/* Orbit Diagram & Selected Detail Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left / Center: Interactive Circular Orbit Graphic */}
          <div className="lg:col-span-6 flex justify-center py-6">
            <div className="relative h-80 w-80 sm:h-96 sm:w-96 rounded-full border-2 border-dashed border-amber-300/80 bg-gradient-to-br from-[#FFF9F2] via-white to-[#F0F5FF] flex items-center justify-center shadow-inner">
              {/* Inner Orbit Circle */}
              <div className="h-44 w-44 sm:h-52 sm:w-52 rounded-full border border-amber-200 bg-amber-50/50 flex flex-col items-center justify-center p-4 text-center shadow-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0B3060] text-white mb-1 shadow">
                  <Sparkles size={18} className="text-amber-300" />
                </div>
                <span className="text-12 font-extrabold text-[#0B3060] leading-tight">
                  Karmayogi Ecosystem
                </span>
                <span className="text-10 text-slate-500 mt-0.5 font-medium">Click any node</span>
              </div>

              {/* 6 Hub Nodes Around Orbit */}
              {HUBS.map((hub) => {
                const Icon = hub.icon
                const isSelected = selectedHub.id === hub.id
                return (
                  <button
                    key={hub.id}
                    type="button"
                    onClick={() => setSelectedHub(hub)}
                    className={`absolute flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-full shadow-lg transition-all transform ${
                      hub.position
                    } ${hub.color} ${
                      isSelected
                        ? 'ring-4 ring-amber-400 ring-offset-2 scale-125 z-20 shadow-2xl'
                        : 'hover:scale-110 hover:shadow-xl opacity-90 z-10'
                    }`}
                    title={hub.name}
                  >
                    <Icon size={20} />
                  </button>
                )
              })}
            </div>
          </div>

          {/* Right: Selected Hub Details Spotlight */}
          <div className="lg:col-span-6">
            <div className="overflow-hidden rounded-2xl border-2 border-amber-200 bg-gradient-to-br from-[#FFFDF9] to-[#FFF7ED] p-7 shadow-xl space-y-5">
              <div className="flex items-center justify-between border-b border-amber-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0B3060] text-amber-300 shadow">
                    <selectedHub.icon size={26} />
                  </div>
                  <div>
                    <span className="text-11 font-bold uppercase tracking-wider text-[#D96B0B]">
                      {selectedHub.tagline}
                    </span>
                    <h3 className="text-22 font-extrabold text-[#0B3060]">
                      {selectedHub.name}
                    </h3>
                  </div>
                </div>
                <span className="rounded-full bg-amber-100 text-amber-900 font-mono text-11 font-bold px-3 py-1 border border-amber-300">
                  Accredited
                </span>
              </div>

              <p className="text-15 text-slate-700 leading-relaxed font-normal">
                {selectedHub.description}
              </p>

              <div className="rounded-xl border border-amber-200 bg-white p-4 shadow-sm space-y-2">
                <div className="text-12 font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Award size={15} className="text-[#F58220]" />
                  Key Capability Indicator
                </div>
                <p className="text-13 text-slate-600 font-medium">
                  {selectedHub.stats}
                </p>
              </div>

              {/* Hub Dots Navigation */}
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-1.5">
                  {HUBS.map((hub) => (
                    <button
                      key={hub.id}
                      type="button"
                      onClick={() => setSelectedHub(hub)}
                      className={`h-2.5 rounded-full transition-all ${
                        hub.id === selectedHub.id ? 'w-8 bg-[#F58220]' : 'w-2.5 bg-slate-300'
                      }`}
                      aria-label={`Select ${hub.name}`}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  onClick={onOpenLogin}
                  className="flex items-center gap-1.5 rounded-lg bg-[#0B3060] px-5 py-2 text-13 font-bold text-white shadow hover:bg-[#F58220] transition-colors"
                >
                  <span>Explore {selectedHub.name}</span>
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Two Bottom Promotional / Quick Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          {/* Card 1: How to Register & Login */}
          <div className="relative overflow-hidden rounded-2xl border border-amber-300 bg-gradient-to-r from-[#FFE5B4] via-[#FFD88A] to-[#FCD34D] p-6 shadow-md flex flex-col justify-between min-h-[170px]">
            <div>
              <span className="text-11 font-bold uppercase tracking-wider text-amber-900 block mb-1">
                Official Access Guide
              </span>
              <h3 className="text-19 font-extrabold text-amber-950 leading-snug">
                How to Register & Login at the iGOT Karmayogi Platform?
              </h3>
            </div>

            <div className="pt-4">
              <button
                type="button"
                onClick={onOpenLogin}
                className="flex items-center gap-2 rounded-lg bg-[#0B3060] px-5 py-2 text-13 font-bold text-white shadow hover:bg-[#154399] transition-all"
              >
                <span>How-to Login and Register</span>
                <Play size={14} fill="currentColor" />
              </button>
            </div>
          </div>

          {/* Card 2: iGOT Walkthrough */}
          <div className="relative overflow-hidden rounded-2xl border border-blue-200 bg-gradient-to-r from-[#F0F5FF] via-[#E4EEFF] to-[#D5E5FF] p-6 shadow-md flex flex-col justify-between min-h-[170px]">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-11 font-bold uppercase tracking-wider text-[#0B3060]">
                  Mission Karmayogi
                </span>
              </div>
              <h3 className="text-19 font-extrabold text-[#0B3060] leading-snug">
                iGOT Platform Walkthrough & Feature Tour
              </h3>
              <p className="text-12 text-slate-600 mt-1">
                Explore role profiling, skill gaps, AI question generation, and workforce analytics.
              </p>
            </div>

            <div className="pt-4">
              <button
                type="button"
                onClick={onOpenLogin}
                className="flex items-center gap-2 rounded-lg bg-[#0F54B9] px-5 py-2 text-13 font-bold text-white shadow hover:bg-[#0B3060] transition-all"
              >
                <span>iGOT Walkthrough</span>
                <Play size={14} fill="currentColor" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
