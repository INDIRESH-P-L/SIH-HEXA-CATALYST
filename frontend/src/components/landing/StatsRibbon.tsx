import { Award, BookOpen, Clock, TrendingUp, Users } from 'lucide-react'

const STATS = [
  {
    icon: Users,
    value: '1,72,23,298',
    label: 'Total Enrolments',
  },
  {
    icon: BookOpen,
    value: '6,427',
    subLabel: 'incl. 41 MoSPI modules',
    label: 'Total Courses',
  },
  {
    icon: Clock,
    value: '15,15,14,944',
    label: 'Total Learning Hours',
  },
  {
    icon: TrendingUp,
    value: '16,22,897',
    label: 'Monthly Active Users',
  },
  {
    icon: Award,
    value: '3,29,499',
    label: 'Certifications Issued',
  },
]

export function StatsRibbon() {
  return (
    <section className="bg-gradient-to-r from-[#0B3060] via-[#154399] to-[#0B3060] py-4 px-4 sm:px-6 lg:px-8 shadow-inner border-y border-[#1E52B0]">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 divide-y-2 sm:divide-y-0 sm:divide-x divide-white/10">
          {STATS.map((stat, idx) => {
            const Icon = stat.icon
            return (
              <div
                key={stat.label}
                className={`flex items-center gap-3.5 pt-3 sm:pt-0 ${
                  idx !== 0 ? 'sm:pl-6' : ''
                }`}
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/10 text-white shadow-sm ring-1 ring-white/20">
                  <Icon size={20} className="text-amber-300" />
                </div>
                <div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-mono text-18 sm:text-20 font-extrabold text-white tracking-tight">
                      {stat.value}
                    </span>
                  </div>
                  <p className="text-11 sm:text-12 font-medium text-slate-200 leading-tight">
                    {stat.label}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
