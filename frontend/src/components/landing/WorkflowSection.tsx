import { CheckCircle2, Navigation, FileCheck, ArrowRight } from 'lucide-react'

const WORKFLOW = [
  {
    step: '1',
    title: 'Role Discovery',
    description: 'The officer logs in and their role, cadre, and target competencies are retrieved from the FRAC baseline.',
    icon: Navigation,
  },
  {
    step: '2',
    title: 'Baseline Assessment',
    description: 'An AI-generated, securely proctored assessment accurately scores current knowledge against the FRAC framework.',
    icon: FileCheck,
  },
  {
    step: '3',
    title: 'Personalized Recommendations',
    description: 'Based on identified competency gaps, targeted iGOT courses are recommended to bridge the skill deficit.',
    icon: CheckCircle2,
  },
]

export function WorkflowSection() {
  return (
    <section className="py-24 bg-white border-y border-slate-100">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-32 font-black tracking-tight text-[#0B3060] sm:text-40 mb-6">
              The Upskilling Journey
            </h2>
            <p className="text-16 text-slate-600 leading-relaxed mb-10">
              HEXA-CATALYST provides a seamless, deterministic flow from the moment an officer logs in. Everything is backed by verifiable data rather than self-reported claims.
            </p>

            <div className="space-y-8">
              {WORKFLOW.map((item, index) => (
                <div key={item.step} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#0B3060] text-white font-bold text-16 shadow-md relative z-10">
                      {item.step}
                    </div>
                    {index < WORKFLOW.length - 1 && (
                      <div className="w-0.5 h-full bg-slate-200 my-2" />
                    )}
                  </div>
                  <div className="pt-2">
                    <h4 className="text-18 font-bold text-slate-900 flex items-center gap-2">
                      <item.icon size={20} className="text-[#F58220]" />
                      {item.title}
                    </h4>
                    <p className="mt-2 text-14 text-slate-600 leading-relaxed max-w-md">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-[#0B3060] to-[#154399] rounded-3xl transform rotate-3 scale-105 opacity-10" />
            <div className="relative rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
              <div className="flex justify-between items-center mb-6">
                <span className="text-13 font-bold text-slate-900">Officer Progress</span>
                <span className="bg-emerald-100 text-emerald-800 text-11 font-bold px-2.5 py-1 rounded-full">
                  Real-time Ledger
                </span>
              </div>
              <div className="space-y-4">
                <div className="h-4 w-3/4 bg-slate-100 rounded" />
                <div className="h-4 w-1/2 bg-slate-100 rounded" />
                <div className="h-20 w-full bg-slate-50 border border-slate-100 rounded-lg mt-6 relative overflow-hidden">
                  <div className="absolute left-0 top-0 bottom-0 w-1/3 bg-[#F58220]/20" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <ArrowRight size={24} className="text-[#F58220]" />
                  </div>
                </div>
                <div className="h-4 w-5/6 bg-slate-100 rounded mt-4" />
                <div className="h-4 w-2/3 bg-slate-100 rounded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
