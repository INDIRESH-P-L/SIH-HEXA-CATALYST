import { BrainCircuit, ShieldCheck, Target, BarChart3 } from 'lucide-react'

const FEATURES = [
  {
    icon: ShieldCheck,
    title: 'AI-Proctored Assessments',
    description: 'Secure, automated testing environments with strict security limits, tab-switching detection, and full-screen enforcement to ensure deterministic scoring integrity.',
    color: 'bg-emerald-100 text-emerald-700',
  },
  {
    icon: Target,
    title: 'FRAC Gap Analysis',
    description: 'Precise 4-point scale mapping of an officer\'s current competencies against the required targets for their specific job role and cadre.',
    color: 'bg-indigo-100 text-indigo-700',
  },
  {
    icon: BrainCircuit,
    title: 'AI Trainer Studio',
    description: 'LLM-powered dynamic MCQ generation allowing trainers to seamlessly construct assessments from official documentation and source material.',
    color: 'bg-[#F58220]/20 text-[#D96B0B]',
  },
  {
    icon: BarChart3,
    title: 'Workforce Analytics',
    description: 'K-anonymous, privacy-preserving administrative dashboards providing deep insights into systemic capability gaps and training effectiveness.',
    color: 'bg-[#0B3060]/10 text-[#0B3060]',
  },
]

export function FeaturesGrid() {
  return (
    <section className="py-24 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-32 font-black tracking-tight text-[#0B3060] sm:text-40">
            Core Platform Capabilities
          </h2>
          <p className="mt-4 text-16 text-slate-600 leading-relaxed">
            HEXA-CATALYST replaces manual, subjective evaluations with a deterministic, AI-enabled ledger of competencies.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="group relative overflow-hidden rounded-3xl bg-white p-8 shadow-sm border border-slate-200 transition-all hover:shadow-xl hover:-translate-y-1"
            >
              <div className={`mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl ${feature.color}`}>
                <feature.icon size={28} strokeWidth={1.5} />
              </div>
              <h3 className="mb-3 text-20 font-bold text-slate-900 group-hover:text-[#F58220] transition-colors">
                {feature.title}
              </h3>
              <p className="text-15 text-slate-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
