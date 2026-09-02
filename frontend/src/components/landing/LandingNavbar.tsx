import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Menu, Sparkles, User, X } from 'lucide-react'

import { useAuth } from '../../lib/auth'

interface LandingNavbarProps {
  onOpenLogin: () => void
}

export function LandingNavbar({ onOpenLogin }: LandingNavbarProps) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks: { label: string; href: string }[] = []

  return (
    <header className="sticky top-0 z-40 w-full bg-white shadow-sm border-b border-slate-200/80">
      {/* Top Tricolor Accent Stripe */}
      <div className="tricolor-strip" />

      {/* Main Navigation Bar */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
        {/* Brand & Emblem */}
        <div className="flex items-center gap-3.5">
          <Link to="/" className="flex items-center gap-3 group">
            {/* Karmayogi Emblem SVG */}
            <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#0B3060] to-[#154399] text-white shadow-sm ring-1 ring-black/5">
              <svg viewBox="0 0 24 24" className="h-7 w-7 fill-current" aria-hidden="true">
                {/* Lotus / Chakra stylized emblem */}
                <path d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z" fill="#F58220" opacity="0.9" />
                <circle cx="12" cy="13" r="3.5" fill="#FFFFFF" />
                <circle cx="12" cy="13" r="1.5" fill="#0B3060" />
              </svg>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-16 font-extrabold tracking-tight text-[#0B3060] group-hover:text-[#F58220] transition-colors">
                  HEXA-CATALYST
                </span>
                <span className="text-12 font-bold text-[#F58220]">| MoSPI</span>
              </div>
              <span className="text-11 font-medium text-slate-500 tracking-wide">
                AI-Enabled Skill Intelligence Platform
              </span>
            </div>
          </Link>
        </div>

        {/* Desktop Navigation Links */}
        {navLinks.length > 0 && (
          <nav className="hidden lg:flex items-center gap-6" aria-label="Main Navigation">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-13 font-semibold text-slate-700 hover:text-[#F58220] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </nav>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          {user ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="flex items-center gap-1.5 rounded-full bg-[#0B3060] px-4 py-1.5 text-12 font-bold text-white shadow-sm hover:bg-[#154399] transition-all"
              >
                <User size={14} />
                Officer Dashboard
              </button>
              <button
                type="button"
                onClick={() => signOut()}
                className="rounded-full border border-slate-300 px-3 py-1.5 text-12 font-semibold text-slate-700 hover:bg-slate-100"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <>
              <Link
                to="/login?tab=signup"
                className="rounded-full border-2 border-[#0B3060] bg-white px-5 py-1.5 text-13 font-bold text-[#0B3060] shadow-sm hover:bg-slate-50 transition-all"
              >
                Sign Up
              </Link>
              <button
                type="button"
                onClick={onOpenLogin}
                className="rounded-full border-2 border-transparent bg-slate-100 px-5 py-1.5 text-13 font-bold text-slate-700 shadow-sm hover:bg-slate-200 transition-all"
              >
                Log In
              </button>
              <button
                type="button"
                onClick={onOpenLogin}
                className="rounded-full bg-gradient-to-r from-[#F58220] to-[#E65100] px-5 py-1.5 text-13 font-bold text-white shadow-sm hover:from-[#E65100] hover:to-[#D84315] transition-all flex items-center gap-1.5"
              >
                <Sparkles size={14} />
                Demo Access
              </button>
            </>
          )}

          {/* Mobile Menu Trigger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 py-4 space-y-2 animate-fade-in shadow-lg">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-lg px-3 py-2 text-14 font-semibold text-slate-800 hover:bg-slate-50"
            >
              {link.label}
            </a>
          ))}
          {!user && (
            <div className="pt-2 flex flex-col gap-2">
              <Link
                to="/login?tab=signup"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full rounded-lg border-2 border-[#0B3060] py-2.5 text-14 font-bold text-[#0B3060] text-center"
              >
                Sign Up
              </Link>
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false)
                  onOpenLogin()
                }}
                className="w-full rounded-lg bg-[#0B3060] py-2.5 text-14 font-bold text-white text-center"
              >
                Log In / Launch Demo
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  )
}
