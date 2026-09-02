import { useState } from 'react'
import { ChevronLeft, ChevronRight, Clock, Star, X, CheckCircle } from 'lucide-react'

interface CourseItem {
  id: string
  title: string
  category: string
  provider: string
  duration: string
  level: string
  levelNum: number
  rating: number
  enrolled: string
  description: string
  topics: string[]
  badge: 'iGOT' | 'NSSTA' | 'MoSPI'
  imageBg: string
}

const COURSES: CourseItem[] = [
  {
    id: 'c1',
    title: 'Prevention of Sexual Harassment of Women at Workplace (PoSH)',
    category: 'Governance & Ethics',
    provider: 'By Capacity Building Commission / DoPT',
    duration: '6 hrs',
    level: 'Level 1 · Awareness',
    levelNum: 1,
    rating: 4.8,
    enrolled: '14,28,400',
    description: 'Statutory compliance, ICC mechanisms, definitions, case protocols, and fostering an inclusive workplace in government departments.',
    topics: ['Statutory Mandates', 'Internal Complaints Committee', 'Inquiry Procedure', 'Redressal Framework'],
    badge: 'iGOT',
    imageBg: 'from-blue-900 to-indigo-950',
  },
  {
    id: 'c2',
    title: 'Fire Safety & Emergency Preparedness in Public Facilities',
    category: 'Safety & Administration',
    provider: 'By Ministry of Health & Family Welfare',
    duration: '4 hrs',
    level: 'Level 1 · Awareness',
    levelNum: 1,
    rating: 4.7,
    enrolled: '8,92,300',
    description: 'Facility safety protocols, evacuation maps, hazardous material handling, and fire drill checklists for government office complexes.',
    topics: ['Evacuation Routes', 'Fire Extinguisher Classes', 'Emergency Coordination', 'Audit Checklists'],
    badge: 'iGOT',
    imageBg: 'from-amber-900 to-red-950',
  },
  {
    id: 'c3',
    title: 'Civil Defence Services & Community Disaster Response',
    category: 'Disaster Management',
    provider: 'By National Disaster Response Force (NDRF)',
    duration: '12 hrs',
    level: 'Level 2 · Application',
    levelNum: 2,
    rating: 4.8,
    enrolled: '6,45,100',
    description: 'First responder fundamentals, incident command systems, communication lines, and flood/cyclone relief mobilization.',
    topics: ['Incident Command', 'Triage & First Aid', 'Shelter Operations', 'Inter-Agency Coordination'],
    badge: 'NSSTA',
    imageBg: 'from-emerald-900 to-teal-950',
  },
  {
    id: 'c4',
    title: 'SQL Fundamentals for Statistical Analysis & Survey Datasets',
    category: 'Technical / Analytics',
    provider: 'By Data Informatics & Innovation Division (DIID)',
    duration: '18 hrs',
    level: 'Level 2 · Application',
    levelNum: 2,
    rating: 4.9,
    enrolled: '3,84,200',
    description: 'PostgreSQL queries, window functions, aggregations, joins, and extraction pipelines over NSSO and ASI large survey microdata.',
    topics: ['SELECT & Filtering', 'GROUP BY & HAVING', 'Complex Joins', 'Window Functions', 'Query Optimization'],
    badge: 'MoSPI',
    imageBg: 'from-indigo-900 to-purple-950',
  },
  {
    id: 'c5',
    title: 'Sampling Methods & Survey Design Primer for Official Statistics',
    category: 'Statistical Systems',
    provider: 'By National Statistical Systems Training Academy (NSSTA)',
    duration: '24 hrs',
    level: 'Level 3 · Leveraging',
    levelNum: 3,
    rating: 4.9,
    enrolled: '2,19,800',
    description: 'Stratified multistage sampling, survey weights, design effect, non-sampling error mitigation, and frame construction.',
    topics: ['Stratified Sampling', 'Multistage PPS', 'Weight Calibration', 'Design Effect & Variance'],
    badge: 'NSSTA',
    imageBg: 'from-blue-950 to-slate-900',
  },
  {
    id: 'c6',
    title: 'National Data Quality Framework (NDQF) & Metadata Standards',
    category: 'Digital Governance',
    provider: 'By Ministry of Statistics & Programme Implementation',
    duration: '16 hrs',
    level: 'Level 3 · Leveraging',
    levelNum: 3,
    rating: 4.8,
    enrolled: '1,78,600',
    description: 'UN National Quality Assurance Framework (NQAF), SDMX metadata schema, statistical integrity, and dissemination protocols.',
    topics: ['NQAF Dimensions', 'SDMX Registries', 'Data Validation Rules', 'Release Calendars'],
    badge: 'MoSPI',
    imageBg: 'from-slate-900 to-amber-950',
  },
]

export function ShowcasedCourses({ onOpenLogin }: { onOpenLogin: () => void }) {
  const [startIndex, setStartIndex] = useState(0)
  const [selectedCourse, setSelectedCourse] = useState<CourseItem | null>(null)

  const itemsVisible = 4
  const maxStart = Math.max(0, COURSES.length - itemsVisible)

  function nextSlide() {
    setStartIndex((prev) => (prev + 1 > maxStart ? 0 : prev + 1))
  }

  function prevSlide() {
    setStartIndex((prev) => (prev - 1 < 0 ? maxStart : prev - 1))
  }

  const visibleCourses = COURSES.slice(startIndex, startIndex + itemsVisible)

  return (
    <section id="courses" className="karmayogi-pattern py-12 px-4 sm:px-6 lg:px-8 border-y border-amber-200/60">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header with Title and View All */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-24 sm:text-28 font-extrabold text-[#0B3060]">Showcased Courses</h2>
            <p className="text-13 text-slate-600">
              Accredited capacity building modules from iGOT Karmayogi, NSSTA Academy and MoSPI
            </p>
          </div>
          <button
            type="button"
            onClick={onOpenLogin}
            className="text-13 font-bold text-[#D96B0B] hover:text-[#0B3060] transition-colors"
          >
            Show all (41) →
          </button>
        </div>

        {/* Carousel Container */}
        <div className="relative">
          {/* Left Arrow */}
          <button
            type="button"
            onClick={prevSlide}
            aria-label="Previous courses"
            className="absolute -left-3 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/80 text-white shadow-lg hover:bg-black transition-all"
          >
            <ChevronLeft size={22} />
          </button>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {visibleCourses.map((course) => (
              <div
                key={course.id}
                onClick={() => setSelectedCourse(course)}
                className="group cursor-pointer overflow-hidden rounded-xl border border-amber-200/90 bg-white shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Card Thumbnail / Banner Graphic */}
                  <div className={`relative h-40 w-full bg-gradient-to-br ${course.imageBg} p-4 flex flex-col justify-between text-white`}>
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-white/20 backdrop-blur px-2 py-0.5 text-10 font-bold uppercase tracking-wider text-amber-300">
                        {course.category}
                      </span>
                      <span className="flex items-center gap-1 text-11 text-amber-300 font-bold bg-black/30 px-2 py-0.5 rounded">
                        <Clock size={12} /> {course.duration}
                      </span>
                    </div>

                    <div>
                      <span className="inline-block rounded-full bg-[#F58220] px-2.5 py-0.5 text-10 font-extrabold text-white shadow-sm mb-1">
                        {course.badge} Course
                      </span>
                      <h3 className="text-14 font-bold text-white leading-snug line-clamp-2 drop-shadow">
                        {course.title}
                      </h3>
                    </div>
                  </div>

                  {/* Card Details */}
                  <div className="p-4 space-y-2">
                    <p className="text-11 text-slate-500 font-medium truncate">
                      {course.provider}
                    </p>

                    <div className="flex items-center justify-between text-12 pt-1 border-t border-slate-100">
                      <span className="font-semibold text-slate-700">{course.level}</span>
                      <div className="flex items-center gap-1 text-amber-500 font-bold font-mono">
                        <Star size={13} fill="currentColor" /> {course.rating}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Enrol button */}
                <div className="p-4 pt-0">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      onOpenLogin()
                    }}
                    className="w-full rounded-lg bg-slate-50 py-2 text-12 font-bold text-[#0B3060] border border-slate-200 group-hover:bg-[#0B3060] group-hover:text-white transition-all text-center"
                  >
                    View Curriculum & Enrol →
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Right Arrow */}
          <button
            type="button"
            onClick={nextSlide}
            aria-label="Next courses"
            className="absolute -right-3 top-1/2 z-10 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/80 text-white shadow-lg hover:bg-black transition-all"
          >
            <ChevronRight size={22} />
          </button>
        </div>

        {/* Selected Course Modal */}
        {selectedCourse && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
            <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl">
              <div className="tricolor-strip" />
              <div className="flex items-center justify-between border-b border-slate-100 bg-[#FFF7ED] px-6 py-4">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-[#0B3060] px-2 py-0.5 text-11 font-bold text-white">
                    {selectedCourse.badge} Verified
                  </span>
                  <span className="text-12 font-semibold text-slate-600">{selectedCourse.category}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedCourse(null)}
                  className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <h3 className="text-18 font-extrabold text-[#0B3060] leading-snug">
                  {selectedCourse.title}
                </h3>
                <p className="text-12 text-slate-500 font-medium">{selectedCourse.provider}</p>

                <p className="text-13 text-slate-700 leading-relaxed">
                  {selectedCourse.description}
                </p>

                <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200 space-y-2">
                  <span className="text-11 font-bold uppercase tracking-wider text-slate-600 block">
                    Curriculum Topics Covered
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCourse.topics.map((t) => (
                      <span key={t} className="flex items-center gap-1 rounded bg-white px-2 py-1 text-11 font-medium text-slate-800 border border-slate-200 shadow-2xs">
                        <CheckCircle size={11} className="text-emerald-600" /> {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between text-12 text-slate-600 pt-2">
                  <span>⏱️ Duration: <strong>{selectedCourse.duration}</strong></span>
                  <span>👥 Enrolled: <strong>{selectedCourse.enrolled}</strong></span>
                  <span>⭐ Rating: <strong>{selectedCourse.rating} / 5.0</strong></span>
                </div>

                <div className="pt-3">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedCourse(null)
                      onOpenLogin()
                    }}
                    className="w-full rounded-lg bg-[#0B3060] py-2.5 text-14 font-bold text-white shadow hover:bg-[#F58220] transition-colors text-center"
                  >
                    Log In to Enrol & Take Skill Assessment
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
