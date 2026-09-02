import { useState } from 'react'

import { LandingNavbar } from '../components/landing/LandingNavbar'
import { HeroSection } from '../components/landing/HeroSection'
import { FeaturesGrid } from '../components/landing/FeaturesGrid'
import { WorkflowSection } from '../components/landing/WorkflowSection'
import { LandingFooter } from '../components/landing/LandingFooter'
import { QuickLoginModal } from '../components/landing/QuickLoginModal'

export default function LandingPage() {
  const [loginModalOpen, setLoginModalOpen] = useState(false)

  function handleOpenLogin() {
    setLoginModalOpen(true)
  }

  function handleCloseLogin() {
    setLoginModalOpen(false)
  }

  return (
    <div className="min-h-screen bg-white font-sans text-slate-900 selection:bg-[#F58220]/20 selection:text-[#0B3060]">
      {/* Top Navbar */}
      <LandingNavbar onOpenLogin={handleOpenLogin} />

      {/* Hero Section */}
      <HeroSection onOpenLogin={handleOpenLogin} />

      {/* Features Grid */}
      <FeaturesGrid />

      {/* Workflow Section */}
      <WorkflowSection />

      {/* Official Government Footer */}
      <LandingFooter />

      {/* 1-Click Demo / Login Modal */}
      <QuickLoginModal isOpen={loginModalOpen} onClose={handleCloseLogin} />
    </div>
  )
}
