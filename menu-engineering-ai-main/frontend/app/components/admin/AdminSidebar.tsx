"use client"

import { LayoutDashboard, Database, Cpu, History, ShieldAlert, ArrowLeft } from "lucide-react"
import Link from "next/link"

type Props = {
  activeSection: string
  setActiveSection: (section: string) => void
}

const sections = [
  {
    id: "overview",
    label: "Overview",
    icon: LayoutDashboard
  },
  {
    id: "database",
    label: "Database",
    icon: Database
  },
  {
    id: "ai-models",
    label: "AI Models",
    icon: Cpu
  },
  {
    id: "uploads",
    label: "Recent Uploads",
    icon: History
  }
]

export default function AdminSidebar({
  activeSection,
  setActiveSection
}: Props) {
  return (
    <div className="w-72 h-screen bg-card border-r border-border p-6 sticky top-0 shrink-0 flex flex-col justify-between transition-colors duration-300">
      <div>
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-red-500/10 border border-red-500/20 text-red-500 rounded-lg">
              <ShieldAlert size={18} />
            </span>
            <h2 className="text-xl font-bold text-foreground leading-tight">
              10xMenu Admin
            </h2>
          </div>
          <p className="text-muted-foreground text-xs mt-2 font-mono uppercase tracking-widest">
            Platform Control Center
          </p>
        </div>

        {/* Navigation Sidebar Buttons */}
        <div className="space-y-3">
          {sections.map((sec) => {
            const Icon = sec.icon
            return (
              <button
                key={sec.id}
                onClick={() => setActiveSection(sec.id)}
                className={`w-full text-left px-4 py-3.5 rounded-xl border hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 ${
                  activeSection === sec.id
                    ? "bg-primary/10 border-primary/30 text-primary shadow-sm"
                    : "bg-card border-border text-muted-foreground hover:bg-muted hover:text-foreground hover:shadow-sm"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={18} className="shrink-0" />
                  <span className="font-semibold text-sm leading-relaxed">
                    {sec.label}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>
 
      {/* Return to Dashboard Link */}
      <div className="mt-auto border-t border-border pt-4">
        <Link
          href="/menu-engineering"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground hover:scale-[1.03] active:scale-95 font-medium transition duration-200"
        >
          <ArrowLeft size={16} />
          <span>Exit Admin Portal</span>
        </Link>
      </div>
    </div>
  )
}
