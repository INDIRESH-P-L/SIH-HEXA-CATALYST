import { useState, useEffect } from 'react'
import { ArrowRight, ChevronRight, CheckCircle, Database, Lock, Search } from 'lucide-react'

const HERO_SLIDES = [
  {
    tag: 'Intelligence Platform',
    title: 'AI-Enabled Skill Intelligence Platform',
    description: 'Transforming capacity building for MoSPI through deterministic competency mapping, AI-proctored assessments, and precise gap analysis.',
    badge: 'MoSPI 2026',
    graphic: 'radar',
  },
  {
    tag: 'FRAC Framework',
    title: 'Deterministic Competency Mapping',
    description: 'Eliminating subjective self-reporting. Officers are rigorously assessed on a 4-point FRAC scale to ensure alignment with their target role.',
    badge: 'Evidence-Based',
    graphic: 'quiz',
  },
]

export function HeroSection({ onOpenLogin }: { onOpenLogin: () => void }) {
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % HERO_SLIDES.length)
    }, 6000)
    return () => clearInterval(timer)
  }, [])

  const slide = HERO_SLIDES[currentSlide]

  if (!slide) return null;

  return (
    <section className="relative overflow-hidden bg-[#F4F6F9] pt-28 pb-20 lg:pt-36 lg:pb-28">
      {/* Background Decor */}
      <div className="absolute left-0 top-0 w-full h-full overflow-hidden z-0">
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-gradient-to-br from-[#0B3060]/10 to-[#F58220]/5 blur-3xl" />
        <div className="absolute top-1/2 -left-24 h-64 w-64 rounded-full bg-gradient-to-tr from-[#154399]/10 to-transparent blur-2xl" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:gap-8 items-center">
          
          {/* Left Column: Copy & Actions */}
          <div className="lg:col-span-7">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#0B3060]/10 bg-[#0B3060]/5 px-3 py-1 text-12 font-bold text-[#0B3060]">
              <span className="flex h-2 w-2 rounded-full bg-[#F58220]" />
              Smart India Hackathon 2026 Winner
            </div>

            <h1 className="text-40 sm:text-56 font-black tracking-tight text-slate-900 leading-[1.1]">
              Next-Generation <span className="text-[#0B3060]">Workforce Analytics</span> for Government
            </h1>
            
            <p className="mt-6 text-16 sm:text-18 leading-relaxed text-slate-600 max-w-2xl">
              HEXA-CATALYST provides a comprehensive platform for the Ministry of Statistics and Programme Implementation (MoSPI). Seamlessly integrate FRAC competency tracking, secure AI proctoring, and data-driven training recommendations.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={onOpenLogin}
                className="flex items-center gap-2 rounded-full bg-[#0B3060] px-6 py-3 text-14 font-bold text-white shadow-lg hover:bg-[#F58220] transition-colors"
              >
                <span>Launch Skill Intelligence</span>
                <ArrowRight size={17} />
              </button>

              <button
                type="button"
                onClick={onOpenLogin}
                className="flex items-center gap-2 rounded-full border-2 border-slate-300 bg-white/90 backdrop-blur px-6 py-3 text-14 font-bold text-slate-700 shadow-sm hover:border-[#F58220] hover:bg-white transition-all"
              >
                <span>Explore FRAC Model</span>
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="mt-8 flex items-center gap-6 text-12 text-slate-600 font-medium">
              <span className="flex items-center gap-1.5">
                <Database size={15} className="text-emerald-600" />
                Local Datastore
              </span>
              <span className="flex items-center gap-1.5">
                <Lock size={15} className="text-emerald-600" />
                Strict Proctoring
              </span>
              <span className="flex items-center gap-1.5">
                <Search size={15} className="text-emerald-600" />
                K-Anonymous
              </span>
            </div>
          </div>

          {/* Right Column: Featured Graphic Preview */}
          <div className="lg:col-span-5">
            <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl transition-all">
              {/* Card Header */}
              <div className="bg-gradient-to-r from-[#0B3060] to-[#154399] px-6 py-5 text-white relative">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-11 font-bold uppercase tracking-widest text-amber-300 block mb-1">
                      {slide.tag}
                    </span>
                    <span className="text-16 font-black tracking-tight text-white">
                      {slide.title}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-6 bg-slate-50 min-h-[220px] flex flex-col justify-between">
                <p className="text-14 text-slate-600 leading-relaxed mb-6">
                  {slide.description}
                </p>

                {/* Visual Snapshot Preview */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm mb-4">
                  {slide.graphic === 'radar' && (
                    <div className="space-y-3">
                      <div className="flex justify-between text-11 font-semibold text-slate-700">
                        <span>Role: Statistical Officer</span>
                        <span className="text-emerald-700">FRAC Profile</span>
                      </div>
                      <div className="space-y-2">
                        <div>
                          <div className="flex justify-between text-10 text-slate-500 mb-1">
                            <span>Data Analysis</span>
                            <span className="text-red-600 font-bold">L1 / T4</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full bg-red-500 w-1/4 rounded-full" />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-10 text-slate-500 mb-1">
                            <span>Survey Design</span>
                            <span className="text-amber-600 font-bold">L2 / T3</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full bg-amber-500 w-2/3 rounded-full" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {slide.graphic === 'quiz' && (
                    <div className="flex items-center justify-between p-2">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                          <CheckCircle size={20} />
                        </div>
                        <div>
                          <div className="text-12 font-bold text-slate-900">Security Passed</div>
                          <div className="text-10 text-slate-500">Screen share active, focused</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                <div className="flex justify-center gap-2 pt-2">
                  {HERO_SLIDES.map((_, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setCurrentSlide(idx)}
                      className={`h-1.5 rounded-full transition-all ${
                        idx === currentSlide ? 'w-6 bg-[#0B3060]' : 'w-2 bg-slate-300'
                      }`}
                      aria-label={`Go to slide ${idx + 1}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
