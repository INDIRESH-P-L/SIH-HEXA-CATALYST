import { Mail, Phone } from 'lucide-react'

export function LandingFooter() {
  return (
    <footer className="bg-[#071E3D] text-white pt-12 pb-8 px-4 sm:px-6 lg:px-8 border-t-4 border-[#F58220]">
      <div className="mx-auto max-w-7xl space-y-10">
        {/* Main Footer Links Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Col 1: Government Branding (2 Cols) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-white/10 text-white shadow ring-1 ring-white/20">
                <svg viewBox="0 0 24 24" className="h-7 w-7 fill-current" aria-hidden="true">
                  <path d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z" fill="#F58220" />
                  <circle cx="12" cy="13" r="3.5" fill="#FFFFFF" />
                  <circle cx="12" cy="13" r="1.5" fill="#071E3D" />
                </svg>
              </div>
              <div>
                <span className="text-16 font-extrabold text-white block tracking-tight">
                  कर्मयोगी भारत | iGOT
                </span>
                <span className="text-12 font-medium text-amber-300">
                  Capacity Building Commission & MoSPI
                </span>
              </div>
            </div>

            <p className="text-13 text-slate-300 leading-relaxed max-w-sm">
              AI-Enabled Skill Intelligence Platform for deterministic competency profiling, skill-gap analysis, and course recommendation across India’s Official Statistical System.
            </p>

            <div className="pt-1 text-12 text-slate-400 space-y-1">
              <p>🏛️ Data Informatics & Innovation Division (DIID), MoSPI</p>
              <p>🎓 National Statistical Systems Training Academy (NSSTA)</p>
            </div>
          </div>

          {/* Col 2: FRAC Architecture */}
          <div className="space-y-3">
            <h4 className="text-13 font-bold uppercase tracking-wider text-amber-300">
              FRAC Architecture
            </h4>
            <ul className="space-y-2 text-13 text-slate-300">
              <li><span className="hover:text-white transition-colors cursor-pointer">FRAC 4-Point Scale</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">33 Competencies & 4 Domains</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">5 Statistical Job Roles</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">18 Activity Mappings</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Immutable Sealed Versions</span></li>
            </ul>
          </div>

          {/* Col 3: Seams & AI Engine */}
          <div className="space-y-3">
            <h4 className="text-13 font-bold uppercase tracking-wider text-amber-300">
              Deterministic Core
            </h4>
            <ul className="space-y-2 text-13 text-slate-300">
              <li><span className="hover:text-white transition-colors cursor-pointer">Skill-Gap Priority Formula</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Reciprocal Rank Fusion (RRF)</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">10-Gate MCQ Verification</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Difficulty-Weighted Scoring</span></li>
              <li><span className="hover:text-white transition-colors cursor-pointer">Append-Only Event Store</span></li>
            </ul>
          </div>

          {/* Col 4: Contact & Helpdesk */}
          <div className="space-y-3">
            <h4 className="text-13 font-bold uppercase tracking-wider text-amber-300">
              Helpdesk & Support
            </h4>
            <div className="space-y-2 text-13 text-slate-300">
              <p className="flex items-center gap-2">
                <Mail size={14} className="text-amber-400 shrink-0" />
                <span>support.igot@mospi.gov.in</span>
              </p>
              <p className="flex items-center gap-2">
                <Phone size={14} className="text-amber-400 shrink-0" />
                <span>1800-11-KARM (Toll-Free)</span>
              </p>
              <p className="pt-2 text-11 text-slate-400">
                Operating Hours: 09:00 AM - 06:00 PM IST (Mon - Fri)
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-700/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-12 text-slate-400">
          <p>© 2026 Ministry of Statistics and Programme Implementation. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="hover:text-slate-200 cursor-pointer">Privacy Policy</span>
            <span>•</span>
            <span className="hover:text-slate-200 cursor-pointer">Terms of Use</span>
            <span>•</span>
            <span className="hover:text-slate-200 cursor-pointer">Accessibility Statement</span>
            <span>•</span>
            <span className="text-amber-400 font-semibold">Smart India Hackathon 2026</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
