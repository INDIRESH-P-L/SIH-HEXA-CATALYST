import { useState } from 'react'

import { LandingNavbar } from '../components/landing/LandingNavbar'
import { HeroSection } from '../components/landing/HeroSection'
import { StatsRibbon } from '../components/landing/StatsRibbon'
import { DashboardPanels } from '../components/landing/DashboardPanels'
import { ShowcasedCourses } from '../components/landing/ShowcasedCourses'
import { AmritGyaanKosh } from '../components/landing/AmritGyaanKosh'
import { VideoGallery } from '../components/landing/VideoGallery'
import { KarmayogiHubs } from '../components/landing/KarmayogiHubs'
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

      {/* Stats Ribbon */}
      <StatsRibbon />

      {/* 5-Card Dashboard Analytics */}
      <DashboardPanels />

      {/* Showcased Courses Carousel */}
      <ShowcasedCourses onOpenLogin={handleOpenLogin} />

      {/* Amrit Gyaan Kosh Case Studies */}
      <AmritGyaanKosh onOpenLogin={handleOpenLogin} />

      {/* Video Gallery */}
      <VideoGallery onOpenLogin={handleOpenLogin} />

      {/* Karmayogi 6-Hub Ecosystem */}
      <KarmayogiHubs onOpenLogin={handleOpenLogin} />

      {/* Official Government Footer */}
      <LandingFooter />

      {/* 1-Click Demo / Login Modal */}
      <QuickLoginModal isOpen={loginModalOpen} onClose={handleCloseLogin} />
    </div>
  )
}
