"use client"

import Navbar from "../components/Navbar"
import AnimatedBackground from "../components/AnimatedBackground"
import AdminShell from "../components/admin/AdminShell"

export default function AdminPage() {
  return (
    <div className="min-h-screen relative bg-[#020617] text-white">
      <AnimatedBackground />
      <Navbar />

      <div className="relative z-10 font-sans">
        <AdminShell />
      </div>
    </div>
  )
}
