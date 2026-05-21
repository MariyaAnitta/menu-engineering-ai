"use client"

import LoadingScreen from "../components/LoadingScreen"

export default function AdminLoading() {
  return (
    <div className="min-h-screen relative bg-[#020617] text-white flex items-center justify-center">
      <LoadingScreen 
        title="Loading Admin Portal..."
        subtitle="Preparing configuration workspace"
      />
    </div>
  )
}
