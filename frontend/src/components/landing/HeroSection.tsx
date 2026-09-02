import { useState, useEffect } from 'react'
import { ArrowRight, Award, BookOpen, CheckCircle, ChevronRight } from 'lucide-react'

interface HeroSectionProps {
  onOpenLogin: () => void
}

const HERO_SLIDES = [
  {
    tag: 'MISSION KARMAYOGI · NPCSCB',
    title: 'Transforming Civil Services with AI Skill Intelligence',
    description: 'Deterministic competency profiling, automated gap analysis, and tailored course pathways for 43+ Lakh officials.',
    badge: 'FRAC 4-Point Scale',
    accentColor: 'from-[#0B3060] to-[#154399]',
    graphic: 'radar',
  },
  {
    tag: 'DETERMINISTIC RECOMMENDATIONS',
    title: 'Personalised Learning Pathways across iGOT & NSSTA',
    description: 'Semantic + lexical retrieval fusion with prerequisite sequencing mapped directly to officers’ exact skill gaps.',
    badge: '41 Statistical Modules',
    accentColor: 'from-[#D96B0B] to-[#F58220]',
    graphic: 'courses',
  },
  {
    tag: 'AI AT THE EDGES · DETERMINISTIC CORE',
    title: 'Verified AI Assessments with SME Cut-Scores',
    description: 'MCQ generation from uploaded training manuals with 10 deterministic validation gates and closed-loop competency updates.',
    badge: '10 Verification Gates',
    accentColor: 'from-[#046A38] to-[#0A8754]',
    graphic: 'quiz',
  },
]

export function HeroSection({ onOpenLogin }: HeroSectionProps) {
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % HERO_SLIDES.length)
    }, 6000)
    return () => clearInterval(timer)
  }, [])

  const slide = HERO_SLIDES[currentSlide] ?? HERO_SLIDES[0]!

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-[#FFF7ED] via-[#FFF3E3] to-[#FFEAD4] pt-8 pb-14 px-4 sm:px-6 lg:px-8 border-b border-amber-200/60">
      {/* Subtle geometric background accents */}
      <div className="absolute top-0 right-0 -mr-20 -mt-20 h-96 w-96 rounded-full bg-gradient-to-br from-[#F58220]/10 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 h-96 w-96 rounded-full bg-gradient-to-tr from-[#0B3060]/10 to-transparent blur-3xl pointer-events-none" />

      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Headline & Subtext */}
          <div className="lg:col-span-7 space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50/80 px-3.5 py-1 shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-[#F58220] animate-pulse" />
              <span className="text-12 font-bold uppercase tracking-wider text-[#D96B0B]">
                iGOT Karmayogi · Capacity Building Commission
              </span>
            </div>

            <h1 className="text-36 sm:text-44 lg:text-48 font-extrabold tracking-tight text-[#E65100] leading-[1.15]">
              Transforming government officials,{' '}
              <span className="text-[#C62828] block sm:inline">Transforming India</span>
            </h1>

            <p className="text-16 sm:text-17 text-slate-700 font-normal leading-relaxed max-w-2xl">
              Deterministic skill-gap analysis, semantic course recommendation, and AI-generated assessments for officials in India’s Official Statistical System.
            </p>

            {/* Social / Channel Icons */}
            <div className="pt-1">
              <span className="block text-11 font-semibold uppercase tracking-wider text-slate-500 mb-2">
                Follow Us
              </span>
              <div className="flex items-center gap-2.5">
                {[
                  { name: 'Portal', label: '🌐', bg: 'bg-[#154399]' },
                  { name: 'LinkedIn', label: 'in', bg: 'bg-[#0077B5]' },
                  { name: 'YouTube', label: '▶', bg: 'bg-[#FF0000]' },
                  { name: 'Twitter / X', label: '𝕏', bg: 'bg-[#111111]' },
                  { name: 'Facebook', label: 'f', bg: 'bg-[#1877F2]' },
                ].map((item) => (
                  <button
                    key={item.name}
                    type="button"
                    title={item.name}
                    className={`flex h-8 w-8 items-center justify-center rounded-full text-white text-12 font-bold shadow-sm transition-transform hover:scale-110 ${item.bg}`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3.5 pt-2">
              <button
                type="button"
                onClick={onOpenLogin}
                className="flex items-center gap-2 rounded-full bg-gradient-to-r from-[#0B3060] to-[#154399] px-7 py-3 text-15 font-bold text-white shadow-lg hover:shadow-xl hover:from-[#154399] hover:to-[#0B3060] transition-all transform hover:-translate-y-0.5"
              >
                <span>Launch Skill Intelligence</span>
                <ArrowRight size={17} />
              </button>

              <a
                href="#rule-to-role"
                className="flex items-center gap-2 rounded-full border-2 border-slate-300 bg-white/90 backdrop-blur px-6 py-3 text-14 font-bold text-[#0B3060] shadow-sm hover:border-[#F58220] hover:bg-white transition-all"
              >
                <span>Explore FRAC Model</span>
                <ChevronRight size={16} />
              </a>
            </div>

            <div className="flex items-center gap-6 pt-2 text-12 text-slate-600 font-medium">
              <span className="flex items-center gap-1.5">
                <CheckCircle size={15} className="text-emerald-600" />
                No Groq key required (Offline fallback)
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle size={15} className="text-emerald-600" />
                Zero external dependencies
              </span>
            </div>
          </div>

          {/* Right Column: Featured Mission Karmayogi Card & Banner */}
          <div className="lg:col-span-5">
            <div className="relative overflow-hidden rounded-2xl border border-amber-200/90 bg-white shadow-2xl transition-all">
              {/* Card Header with Saffron & Royal Blue Accents */}
              <div className="bg-gradient-to-r from-[#0B3060] via-[#154399] to-[#0B3060] px-6 py-5 text-white relative">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 backdrop-blur border border-white/20">
                      <Award className="h-5 w-5 text-[#F58220]" />
                    </div>
                    <div>
                      <span className="text-11 font-bold uppercase tracking-widest text-amber-300 block">
                        {slide.tag}
                      </span>
                      <span className="text-15 font-extrabold tracking-tight text-white">
                        Karmayogi Bharat
                      </span>
                    </div>
                  </div>
                  <span className="rounded-full bg-amber-400/20 border border-amber-300/40 px-2.5 py-0.5 text-11 font-bold text-amber-300">
                    {slide.badge}
                  </span>
                </div>
              </div>

              {/* Card Body with Dynamic Graphic Preview */}
              <div className="p-6 space-y-4 bg-gradient-to-b from-white to-amber-50/40 min-h-[260px] flex flex-col justify-between">
                <div>
                  <h3 className="text-18 font-bold text-slate-900 leading-snug">
                    {slide.title}
                  </h3>
                  <p className="mt-2 text-13 text-slate-600 leading-relaxed">
                    {slide.description}
                  </p>
                </div>

                {/* Visual Snapshot Preview */}
                <div className="rounded-xl border border-amber-200 bg-white p-3.5 shadow-sm">
                  {slide.graphic === 'radar' && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-11 font-semibold text-slate-700">
                        <span>Role Profile: Statistical Officer</span>
                        <span className="text-emerald-700 font-bold">FRAC 4-Point Target</span>
                      </div>
                      <div className="space-y-1.5">
                        <div>
                          <div className="flex justify-between text-10 text-slate-500 mb-0.5">
                            <span>SQL & Database Querying</span>
                            <span className="text-red-600 font-bold">Level 1 → Target 4 (CRITICAL)</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full bg-red-500 w-1/4 rounded-full" />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-10 text-slate-500 mb-0.5">
                            <span>Sampling Methods & Survey Design</span>
                            <span className="text-amber-600 font-bold">Level 2 → Target 3 (EMERGING)</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full bg-amber-500 w-2/3 rounded-full" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {slide.graphic === 'courses' && (
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700 shrink-0 font-bold">
                        <BookOpen size={20} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-12 font-bold text-slate-900 truncate block">
                          SQL Fundamentals for Statistical Analysis
                        </span>
                        <span className="text-11 text-slate-500">iGOT Karmayogi · 18h · Level 2</span>
                      </div>
                      <span className="rounded bg-emerald-50 text-emerald-700 text-11 font-bold px-2 py-0.5">
                        Top Pick
                      </span>
                    </div>
                  )}

                  {slide.graphic === 'quiz' && (
                    <div className="flex items-center justify-between text-11">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 font-bold">
                          ✓
                        </span>
                        <span className="font-semibold text-slate-800">10 Validation Checks Passed</span>
                      </div>
                      <span className="font-mono font-bold text-indigo-700">Cut-Score: 80%</span>
                    </div>
                  )}
                </div>

                {/* Footer Controls & Persona Quick Start */}
                <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    {HERO_SLIDES.map((_, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setCurrentSlide(idx)}
                        className={`h-2 rounded-full transition-all ${
                          idx === currentSlide ? 'w-6 bg-[#F58220]' : 'w-2 bg-slate-300'
                        }`}
                        aria-label={`Go to slide ${idx + 1}`}
                      />
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={onOpenLogin}
                    className="inline-flex items-center gap-1 text-12 font-bold text-[#0B3060] hover:text-[#F58220] transition-colors"
                  >
                    <span>Test Demo Personas</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
