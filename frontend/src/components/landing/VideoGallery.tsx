import { useState } from 'react'
import { Play, Video, X } from 'lucide-react'

interface VideoItem {
  id: string
  title: string
  tag: string
  duration: string
  speaker: string
  description: string
  timestamps: { time: string; topic: string }[]
  bgGradient: string
}

const VIDEOS: Record<string, VideoItem[]> = {
  howto: [
    {
      id: 'v1',
      title: 'How to Complete Your Competency Assessment & Sync to SPARROW APAR',
      tag: 'Officer Walkthrough',
      duration: '8:45 mins',
      speaker: 'By Ministry of Statistics & Programme Implementation',
      description: 'Step-by-step guidance on taking proctored deterministic assessments, reviewing skill-gap breakdowns, and linking accredited course certificates to eHRMS annual performance appraisal records.',
      timestamps: [
        { time: '00:00', topic: 'Overview of FRAC 4-Point Competency Scale' },
        { time: '02:15', topic: 'Navigating the Skill Intelligence Dashboard' },
        { time: '04:30', topic: 'Submitting a Quiz & Immediate Feedback Loop' },
        { time: '07:10', topic: 'Exporting Provenance Evidence for SPARROW' },
      ],
      bgGradient: 'from-blue-900 via-indigo-950 to-slate-900',
    },
    {
      id: 'v2',
      title: 'Trainer Console: Generating AI MCQs from Uploaded Training Manuals',
      tag: 'Training Academies',
      duration: '11:20 mins',
      speaker: 'By NSSTA Training Faculty',
      description: 'How NSSTA and ministry trainers upload PDF/DOCX course handouts, trigger the AI generation pipeline, review the 10-gate validation checklist, and approve questions into the master bank.',
      timestamps: [
        { time: '00:00', topic: 'Uploading Document & Text Extraction' },
        { time: '03:40', topic: 'PII Scrubbing & Passkey Integrity' },
        { time: '06:15', topic: 'Reviewing the 10 Validation Checks' },
        { time: '09:00', topic: 'Publishing to the Approved Question Bank' },
      ],
      bgGradient: 'from-purple-900 via-indigo-950 to-slate-900',
    },
  ],
  previews: [
    {
      id: 'v3',
      title: 'Course Preview: SQL Fundamentals for Statistical Analysis',
      tag: 'Course Preview',
      duration: '6:15 mins',
      speaker: 'By DIID Technical Lead',
      description: 'An introductory preview of the 18-hour PostgreSQL microdata query module, showing real NSSO household dataset queries and aggregation formulas.',
      timestamps: [
        { time: '00:00', topic: 'Why SQL is Essential for Official Statistics' },
        { time: '02:00', topic: 'Hands-on Query Workbench Demo' },
        { time: '04:45', topic: 'Mastering GROUP BY & Window Functions' },
      ],
      bgGradient: 'from-amber-900 via-orange-950 to-slate-900',
    },
  ],
  talks: [
    {
      id: 'v4',
      title: 'Mission Karmayogi Keynote: Rule-to-Role Transition in Civil Services',
      tag: 'Leadership Keynote',
      duration: '18:30 mins',
      speaker: 'By Capacity Building Commission',
      description: 'Institutional perspective on transforming civil service competencies, lifelong learning, and building future-ready institutional capacity.',
      timestamps: [
        { time: '00:00', topic: 'The Philosophy of Karmayogi Bharat' },
        { time: '06:00', topic: 'Eliminating Redundancy with FRAC Frameworks' },
        { time: '12:30', topic: 'Viksit Bharat 2047: Data-Driven Governance' },
      ],
      bgGradient: 'from-emerald-900 via-teal-950 to-slate-900',
    },
  ],
}

export function VideoGallery({ onOpenLogin }: { onOpenLogin: () => void }) {
  const [activeTab, setActiveTab] = useState<'howto' | 'previews' | 'talks'>('howto')
  const [playingVideo, setPlayingVideo] = useState<VideoItem | null>(null)

  const videoList = VIDEOS[activeTab] || []
  const mainVideo = videoList[0]

  return (
    <section id="video-gallery" className="bg-gradient-to-b from-[#F8FAFC] via-[#EEF4FF] to-white py-14 px-4 sm:px-6 lg:px-8 border-b border-slate-200">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Title */}
        <div className="text-center space-y-2">
          <h2 className="text-24 sm:text-30 font-extrabold text-[#0B3060]">Video Gallery</h2>
          <p className="text-14 text-slate-600">
            Interactive tutorials, feature walkthroughs, and accredited capacity-building masterclasses
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex justify-center">
          <div className="inline-flex rounded-full border border-slate-300 bg-white p-1 shadow-sm">
            {[
              { id: 'howto', label: 'How-to Videos' },
              { id: 'previews', label: 'Course Previews' },
              { id: 'talks', label: 'Community Talks' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`rounded-full px-5 py-2 text-13 font-bold transition-all ${
                  activeTab === tab.id
                    ? 'bg-[#0B3060] text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Main Video Feature Card */}
        {mainVideo && (
          <div className="overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-xl">
            {/* Top Video Stage */}
            <div className={`relative h-64 sm:h-80 w-full bg-gradient-to-br ${mainVideo.bgGradient} p-6 sm:p-8 flex flex-col justify-between text-white`}>
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/20 backdrop-blur px-3 py-1 text-11 font-bold tracking-wider uppercase text-amber-300">
                  {mainVideo.tag}
                </span>
                <span className="rounded bg-black/40 px-2.5 py-1 text-12 font-mono font-bold">
                  ⏱️ {mainVideo.duration}
                </span>
              </div>

              {/* Play Button Trigger */}
              <div className="flex flex-col items-center justify-center my-auto">
                <button
                  type="button"
                  onClick={() => setPlayingVideo(mainVideo)}
                  className="group flex h-16 w-16 sm:h-20 sm:w-20 items-center justify-center rounded-full bg-[#F58220] text-white shadow-2xl transition-all transform hover:scale-110 hover:bg-[#E65100]"
                  aria-label="Play video"
                >
                  <Play size={28} fill="currentColor" className="ml-1" />
                </button>
                <span className="mt-2 text-12 font-bold text-amber-200 tracking-wide drop-shadow">
                  Click to Watch Guided Walkthrough
                </span>
              </div>

              <div>
                <h3 className="text-18 sm:text-22 font-extrabold text-white leading-tight drop-shadow-md">
                  {mainVideo.title}
                </h3>
                <p className="text-12 text-slate-300 mt-1">{mainVideo.speaker}</p>
              </div>
            </div>

            {/* Bottom Bar: Watch Video Button & Timestamps */}
            <div className="bg-[#0B3060] p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 text-white">
              <button
                type="button"
                onClick={() => setPlayingVideo(mainVideo)}
                className="flex items-center gap-2 rounded-lg bg-[#F58220] px-6 py-2.5 text-13 font-bold text-white shadow hover:bg-[#E65100] transition-colors w-full sm:w-auto justify-center"
              >
                <Play size={16} fill="currentColor" /> Watch Video
              </button>

              <div className="flex items-center gap-4 text-12 text-slate-300 flex-wrap justify-center">
                <span>📍 4 Chapters</span>
                <span>•</span>
                <span>🎓 Official iGOT & MoSPI Framework</span>
                <span>•</span>
                <span>🔒 Free Access</span>
              </div>
            </div>
          </div>
        )}

        {/* Video Player Modal */}
        {playingVideo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md animate-fade-in">
            <div className="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 text-white shadow-2xl">
              <div className="tricolor-strip" />
              <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-4">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-[#F58220] px-2 py-0.5 text-10 font-bold uppercase text-white">
                    {playingVideo.tag}
                  </span>
                  <span className="text-13 font-bold text-slate-200">{playingVideo.title}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setPlayingVideo(null)}
                  className="rounded-full p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Simulated Interactive Video Screen */}
              <div className="p-6 space-y-5 bg-gradient-to-b from-slate-900 to-slate-950">
                <div className="relative h-64 sm:h-72 w-full rounded-xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between overflow-hidden">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                      SIMULATED INTERACTIVE DEMONSTRATION
                    </span>
                    <span className="font-mono">1080p · 60fps</span>
                  </div>

                  <div className="my-auto text-center space-y-2">
                    <div className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-white/10 text-amber-400">
                      <Video size={28} />
                    </div>
                    <p className="text-16 font-extrabold text-white">{playingVideo.title}</p>
                    <p className="text-12 text-slate-400 max-w-lg mx-auto">{playingVideo.description}</p>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-11 font-mono text-slate-400">
                      <span>02:45</span>
                      <span>{playingVideo.duration}</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-[#F58220] w-1/3 rounded-full" />
                    </div>
                  </div>
                </div>

                {/* Video Chapters */}
                <div className="space-y-2">
                  <span className="text-12 font-bold uppercase tracking-wider text-slate-400 block">
                    Interactive Chapter Index
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {playingVideo.timestamps.map((ts) => (
                      <div
                        key={ts.time}
                        className="flex items-center gap-2.5 rounded-lg border border-slate-800 bg-slate-900/80 p-2.5 hover:border-amber-400/40 transition-colors"
                      >
                        <span className="rounded bg-[#F58220]/20 font-mono text-11 font-bold text-amber-300 px-2 py-0.5">
                          {ts.time}
                        </span>
                        <span className="text-12 text-slate-300 font-medium truncate">{ts.topic}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setPlayingVideo(null)
                      onOpenLogin()
                    }}
                    className="w-full rounded-lg bg-gradient-to-r from-[#0B3060] to-[#154399] py-2.5 text-14 font-bold text-white shadow hover:from-[#154399] hover:to-[#0B3060] text-center"
                  >
                    Log In to Access the Full Interactive Video Lab
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
