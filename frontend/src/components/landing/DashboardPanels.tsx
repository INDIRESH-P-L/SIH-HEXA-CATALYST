import { useState } from 'react'
import { Award, Building2, CheckCircle2, FileSpreadsheet, Globe2, Layers, MapPin, TrendingUp, Users } from 'lucide-react'

export function DashboardPanels() {
  const [activeTab, setActiveTab] = useState<'states' | 'ministries'>('ministries')

  return (
    <section id="rule-to-role" className="bg-[#F8FAFC] py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Section Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 border border-blue-200 px-3 py-0.5 text-11 font-bold text-[#0B3060] uppercase tracking-wider">
            <span>Capacity Building Analytics</span>
          </div>
          <h2 className="text-26 sm:text-30 font-extrabold text-[#0B3060]">
            National Competency & Learning Architecture
          </h2>
          <p className="text-14 text-slate-600 max-w-2xl mx-auto">
            Real-time analytics across Union Ministries, State Governments, and Cadre Services powered by the FRAC 4-point model.
          </p>
        </div>

        {/* Top 2 Panels Grid (Rule to Role & Democratised Learning) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Card 1: Rule to Role Based Learning (7 Cols) */}
          <div className="lg:col-span-7 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            {/* Blue Banner Header */}
            <div className="bg-[#0F54B9] px-5 py-3 text-white flex items-center justify-between">
              <h3 className="text-15 font-bold tracking-wide flex items-center gap-2">
                <Layers size={18} className="text-amber-300" />
                Rule to Role Based Learning (FRAC Model)
              </h3>
              <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
                Capacity Building Plans
              </span>
            </div>

            <div className="p-5 space-y-5">
              <div className="text-12 font-bold text-slate-700 uppercase tracking-wider">
                Coverage of Role Relevant Capacity Building Plans (CBPs)
              </div>

              {/* 4 Stat Boxes */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg border border-amber-200 bg-[#FFF9F2] p-3 text-center">
                  <div className="flex justify-center text-[#D96B0B] mb-1">
                    <Building2 size={20} />
                  </div>
                  <div className="font-mono text-18 font-extrabold text-[#0B3060]">1,434</div>
                  <div className="text-11 font-semibold text-slate-600">Union CBPs</div>
                </div>

                <div className="rounded-lg border border-blue-200 bg-[#F0F5FF] p-3 text-center">
                  <div className="flex justify-center text-[#0F54B9] mb-1">
                    <Users size={20} />
                  </div>
                  <div className="font-mono text-18 font-extrabold text-[#0B3060]">43,45,664</div>
                  <div className="text-11 font-semibold text-slate-600">Employees with CBPs</div>
                </div>

                <div className="rounded-lg border border-emerald-200 bg-[#F0FBF5] p-3 text-center">
                  <div className="flex justify-center text-[#046A38] mb-1">
                    <Globe2 size={20} />
                  </div>
                  <div className="font-mono text-18 font-extrabold text-[#0B3060]">2,609</div>
                  <div className="text-11 font-semibold text-slate-600">State CBPs</div>
                </div>

                <div className="rounded-lg border border-purple-200 bg-[#F8F4FF] p-3 text-center">
                  <div className="flex justify-center text-purple-700 mb-1">
                    <FileSpreadsheet size={20} />
                  </div>
                  <div className="font-mono text-18 font-extrabold text-[#0B3060]">12,374,227</div>
                  <div className="text-11 font-semibold text-slate-600">Role Competencies</div>
                </div>
              </div>

              {/* Courses by Competency Level */}
              <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-12 font-bold text-slate-700 block">
                    Courses by Competency Level (FRAC Scale)
                  </span>
                  <p className="text-11 text-slate-500">
                    Distribution of 6,427 accredited offerings across 4 proficiency tiers
                  </p>
                </div>

                {/* Level Pills */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-[#154399]" />
                    <span className="text-11 font-medium text-slate-700">Basic (1): <strong className="font-mono">3,747</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-[#F58220]" />
                    <span className="text-11 font-medium text-slate-700">Inter (2): <strong className="font-mono">1,934</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-[#046A38]" />
                    <span className="text-11 font-medium text-slate-700">Adv (3-4): <strong className="font-mono">431</strong></span>
                  </div>
                </div>
              </div>

              {/* Mini stacked level bar */}
              <div className="h-3 w-full rounded-full bg-slate-100 flex overflow-hidden">
                <div style={{ width: '61%' }} className="bg-[#154399]" title="Basic: 3,747 (61%)" />
                <div style={{ width: '31%' }} className="bg-[#F58220]" title="Intermediate: 1,934 (31%)" />
                <div style={{ width: '8%' }} className="bg-[#046A38]" title="Advanced: 431 (8%)" />
              </div>
            </div>
          </div>

          {/* Card 2: Democratised Learning (5 Cols) */}
          <div className="lg:col-span-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            {/* Blue Banner Header */}
            <div className="bg-[#0F54B9] px-5 py-3 text-white flex items-center justify-between">
              <h3 className="text-15 font-bold tracking-wide flex items-center gap-2">
                <TrendingUp size={18} className="text-amber-300" />
                Democratised Learning
              </h3>
              <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
                By Cadre Group
              </span>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-12 font-bold text-slate-700 uppercase tracking-wider">
                  Onboarding and Learning Participation
                </span>
                <div className="flex items-center gap-3 text-11">
                  <span className="flex items-center gap-1 text-slate-600">
                    <span className="h-2 w-2 rounded-full bg-slate-400" /> Onboarded %
                  </span>
                  <span className="flex items-center gap-1 text-[#0F54B9] font-bold">
                    <span className="h-2 w-2 rounded-full bg-[#0F54B9]" /> Completed %
                  </span>
                </div>
              </div>

              {/* Group Bars */}
              <div className="space-y-3.5 pt-1">
                <div>
                  <div className="flex justify-between text-12 font-semibold text-slate-800 mb-1">
                    <span>Group A (Senior Statistical Officers / Directors)</span>
                    <span className="font-mono text-[#0F54B9] font-bold">88%</span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#0F54B9] to-[#154399] w-[88%]" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-12 font-semibold text-slate-800 mb-1">
                    <span>Group B (Statistical Officers / Investigators)</span>
                    <span className="font-mono text-[#0F54B9] font-bold">82%</span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#0F54B9] to-[#154399] w-[82%]" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-12 font-semibold text-slate-800 mb-1">
                    <span>Group C & Field Staff (Survey Enumerators)</span>
                    <span className="font-mono text-[#0F54B9] font-bold">80%</span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#0F54B9] to-[#154399] w-[80%]" />
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-blue-50/70 border border-blue-100 p-3 mt-4 text-11 text-[#0B3060] leading-relaxed">
                ✨ <strong>Parity Benchmark:</strong> Learning access is democratised across field survey staff and headquarters directorates, achieving 80%+ cross-cadre completion.
              </div>
            </div>
          </div>
        </div>

        {/* Lower 3 Panels Grid (Ranking Map, Shared National Aspirations, Right Person) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Card 3: iGOT Learning Progress Ranking (5 Cols) */}
          <div className="lg:col-span-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
            <div>
              <div className="bg-[#0F54B9] px-5 py-3 text-white flex items-center justify-between">
                <h3 className="text-15 font-bold tracking-wide flex items-center gap-2">
                  <MapPin size={18} className="text-amber-300" />
                  iGOT Learning Progress Ranking
                </h3>
                <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
                  Live Index
                </span>
              </div>

              <div className="p-5 space-y-4">
                {/* Tabs */}
                <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1">
                  <button
                    type="button"
                    onClick={() => setActiveTab('ministries')}
                    className={`flex-1 py-1.5 text-12 font-bold rounded-md transition-all ${
                      activeTab === 'ministries'
                        ? 'bg-white text-[#0B3060] shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Union Ministries & Depts
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('states')}
                    className={`flex-1 py-1.5 text-12 font-bold rounded-md transition-all ${
                      activeTab === 'states'
                        ? 'bg-white text-[#0B3060] shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    States & Field Zones
                  </button>
                </div>

                {activeTab === 'ministries' ? (
                  <div className="space-y-2.5">
                    {[
                      { rank: 1, name: 'Ministry of Statistics and PI (MoSPI)', score: '96.8%', badge: '🥇 Rank 1', trophy: 'text-amber-500' },
                      { rank: 2, name: 'Dept. of Food & Public Distribution', score: '94.2%', badge: '🥈 Rank 2', trophy: 'text-slate-400' },
                      { rank: 3, name: 'Ministry of Mines', score: '91.5%', badge: '🥉 Rank 3', trophy: 'text-amber-700' },
                      { rank: 4, name: 'Department of Personnel & Training', score: '89.7%', badge: 'Top 5', trophy: 'text-slate-400' },
                    ].map((dept) => (
                      <div
                        key={dept.name}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-slate-50/70 hover:bg-amber-50/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className={`text-14 font-extrabold ${dept.trophy}`}>{dept.badge}</span>
                          <span className="text-12 font-semibold text-slate-800 truncate max-w-[220px]">
                            {dept.name}
                          </span>
                        </div>
                        <span className="font-mono text-12 font-bold text-[#0F54B9]">{dept.score}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {[
                      { zone: 'MoSPI Northern Zone (Delhi / NSSO HQ)', coverage: '98.2%', status: 'Leading' },
                      { zone: 'Southern Zone (Bengaluru / Chennai)', coverage: '95.4%', status: 'On Track' },
                      { zone: 'Western Zone (Mumbai / Ahmedabad)', coverage: '93.1%', status: 'On Track' },
                      { zone: 'Eastern Zone (Kolkata / Patna)', coverage: '91.8%', status: 'Active' },
                    ].map((z) => (
                      <div
                        key={z.zone}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-slate-50/70"
                      >
                        <span className="text-12 font-semibold text-slate-800">{z.zone}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-12 font-bold text-emerald-700">{z.coverage}</span>
                          <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-10 font-bold text-emerald-700">
                            {z.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="p-3 bg-slate-50 border-t border-slate-100 text-center text-11 text-slate-500">
              📊 Evaluated on FRAC completion rate, competency assessment coverage & decay score.
            </div>
          </div>

          {/* Card 4: Shared National Aspirations (7 Cols) */}
          <div className="lg:col-span-7 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            <div className="bg-[#0F54B9] px-5 py-3 text-white flex items-center justify-between">
              <h3 className="text-15 font-bold tracking-wide flex items-center gap-2">
                <Award size={18} className="text-amber-300" />
                Shared National Aspirations
              </h3>
              <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
                National Priorities
              </span>
            </div>

            <div className="p-5 space-y-4">
              <div className="text-12 font-bold text-slate-700 uppercase tracking-wider">
                Course Completion for National Priorities
              </div>

              <div className="space-y-3.5">
                {[
                  { label: 'AI & Emerging Tech', count: '1,33,80,712', pct: 92, color: 'from-blue-600 to-indigo-600' },
                  { label: 'Citizen Centricity & Jan Bhagidari', count: '1,50,06,652', pct: 96, color: 'from-amber-500 to-orange-500' },
                  { label: 'Viksit Bharat 2047', count: '1,10,49,297', pct: 84, color: 'from-emerald-600 to-teal-600' },
                  { label: 'Official Statistics & Data Governance', count: '89,45,210', pct: 78, color: 'from-purple-600 to-indigo-700' },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-13 font-semibold text-slate-800">{item.label}</span>
                      <span className="font-mono text-14 font-extrabold text-[#0B3060]">{item.count}</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full bg-gradient-to-r ${item.color}`}
                        style={{ width: `${item.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Card 5: Sub-banner for Right Person for the Right Job */}
              <div className="mt-5 pt-4 border-t border-slate-200">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-13 font-extrabold text-[#0F54B9] flex items-center gap-1.5">
                    <CheckCircle2 size={16} /> Right Person for the Right Job (eHRMS & FRAC Matching)
                  </span>
                  <span className="text-10 text-slate-400 font-mono">Date Last Update On: 02 Sep 2026</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="rounded border border-slate-200 bg-slate-50 p-2">
                    <div className="font-mono text-14 font-extrabold text-slate-900">643,108</div>
                    <div className="text-10 text-slate-500 leading-tight">eHRMS Access</div>
                  </div>
                  <div className="rounded border border-slate-200 bg-slate-50 p-2">
                    <div className="font-mono text-14 font-extrabold text-slate-900">57</div>
                    <div className="text-10 text-slate-500 leading-tight">Cadre Services</div>
                  </div>
                  <div className="rounded border border-slate-200 bg-slate-50 p-2">
                    <div className="font-mono text-14 font-extrabold text-slate-900">8,449</div>
                    <div className="text-10 text-slate-500 leading-tight">Transfer Mappings</div>
                  </div>
                  <div className="rounded border border-slate-200 bg-slate-50 p-2">
                    <div className="font-mono text-14 font-extrabold text-slate-900">303</div>
                    <div className="text-10 text-slate-500 leading-tight">FRAC Matched</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
