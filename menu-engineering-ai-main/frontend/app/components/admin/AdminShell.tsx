"use client"

import { useState, useEffect } from "react"
import { 
  Activity, 
  Database, 
  Cpu, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  ChevronDown, 
  Check, 
  Server, 
  Brain, 
  History, 
  Clock, 
  BarChart3, 
  Layers
} from "lucide-react"
import AdminSidebar from "./AdminSidebar"
import { API_BASE_URL } from "../../config"

// Mock spreadsheet uploads
const mockUploads = [
  {
    id: "upload-1",
    filename: "spice_garden_friday_specials.xlsx",
    status: "Processed",
    timestamp: "2026-05-17 14:23:10",
    rowCount: 20,
    totalRevenue: "₹18,450.00",
    category: "Indian Bistro"
  },
  {
    id: "upload-2",
    filename: "ocean_breeze_seafood_menu.xlsx",
    status: "Processed",
    timestamp: "2026-05-16 11:05:42",
    rowCount: 15,
    totalRevenue: "₹34,200.00",
    category: "Seafood Fine Dining"
  },
  {
    id: "upload-3",
    filename: "mamma_mia_pasta_specialties.xlsx",
    status: "Processed",
    timestamp: "2026-05-15 18:45:12",
    rowCount: 25,
    totalRevenue: "₹22,120.00",
    category: "Traditional Italian"
  },
  {
    id: "upload-4",
    filename: "urban_burger_co_core_menu.xlsx",
    status: "Processed",
    timestamp: "2026-05-14 09:12:00",
    rowCount: 10,
    totalRevenue: "₹9,800.00",
    category: "Gourmet QSR"
  },
  {
    id: "upload-5",
    filename: "sweet_delights_bakery_desserts.xlsx",
    status: "Indexing",
    timestamp: "2026-05-17 17:15:00",
    rowCount: 12,
    totalRevenue: "₹5,400.00",
    category: "Bakery & Desserts"
  }
]

export default function AdminShell() {
  const [activeSection, setActiveSection] = useState("overview")
  const [dbProvider, setDbProvider] = useState("firebase")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<"success" | "error" | null>(null)
  const [statusMessage, setStatusMessage] = useState("")

  // Fetch active provider from backend on mount
  useEffect(() => {
    async function fetchProvider() {
      try {
        const res = await fetch(`${API_BASE_URL}/admin/database-provider`)
        if (res.ok) {
          const data = await res.json()
          if (data && data.provider) {
            setDbProvider(data.provider)
          }
        }
      } catch (error) {
        console.error("Failed to fetch database provider on load:", error)
      }
    }
    fetchProvider()
  }, [])

  const handleSaveConfig = async () => {
    setIsSaving(true)
    setSaveStatus(null)
    setStatusMessage("")
    try {
      const res = await fetch(`${API_BASE_URL}/admin/database-provider`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ provider: dbProvider })
      })
      const data = await res.json()
      if (res.ok && data.status === "success") {
        setSaveStatus("success")
        setStatusMessage(data.message || "Configuration saved successfully!")
      } else {
        setSaveStatus("error")
        setStatusMessage(data.message || "Failed to update configuration.")
      }
    } catch (error) {
      console.error("Save config error:", error)
      setSaveStatus("error")
      setStatusMessage("Network error: failed to connect to backend.")
    } finally {
      setIsSaving(false)
    }
  }

  const [platformMetrics, setPlatformMetrics] = useState<any | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false)

  const fetchPlatformMetrics = async () => {
    if (platformMetrics) return
    setIsLoadingMetrics(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/platform-metrics`)
      if (res.ok) {
        const data = await res.json()
        setPlatformMetrics(data)
      }
    } catch (error) {
      console.error("Failed to fetch platform metrics:", error)
    } finally {
      setIsLoadingMetrics(false)
    }
  }

  const [uploads, setUploads] = useState<any[]>([])
  const [isLoadingUploads, setIsLoadingUploads] = useState(false)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)
  const [pageIndex, setPageIndex] = useState(0)
  const [pageCursors, setPageCursors] = useState<(string | null)[]>([null])
  const [hasMore, setHasMore] = useState(false)

  // Lightweight Caching
  const [pagesCache, setPagesCache] = useState<Record<number, { uploads: any[], nextCursor: string | null, hasMore: boolean }>>({})
  const [detailsCache, setDetailsCache] = useState<Record<string, any>>({})

  const fetchUploadDetails = async (uploadId: string) => {
    if (!uploadId) return
    if (detailsCache[uploadId]) {
      return
    }

    setIsLoadingDetails(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/upload-details/${encodeURIComponent(uploadId)}`)
      if (res.ok) {
        const data = await res.json()
        setDetailsCache(prev => ({
          ...prev,
          [uploadId]: data
        }))
      }
    } catch (error) {
      console.error("Error fetching upload details:", error)
    } finally {
      setIsLoadingDetails(false)
    }
  }

  const fetchUploadsPage = async (pageIdx: number, startAfterId: string | null) => {
    if (pagesCache[pageIdx]) {
      const cached = pagesCache[pageIdx]
      setUploads(cached.uploads)
      setHasMore(cached.hasMore)
      if (cached.uploads.length > 0) {
        const firstId = cached.uploads[0].upload_id
        setSelectedUploadId(firstId)
        fetchUploadDetails(firstId)
      } else {
        setSelectedUploadId(null)
      }
      return
    }

    setIsLoadingUploads(true)
    try {
      let url = `${API_BASE_URL}/admin/uploads?limit=5`
      if (startAfterId) {
        url += `&start_after_id=${encodeURIComponent(startAfterId)}`
      }
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        const fetchedUploads = data.uploads || []
        const fetchedHasMore = data.has_more || false
        const nextCursor = data.next_page_cursor || null

        setUploads(fetchedUploads)
        setHasMore(fetchedHasMore)

        if (nextCursor) {
          setPageCursors(prev => {
            const nextCursors = [...prev]
            nextCursors[pageIdx + 1] = nextCursor
            return nextCursors
          })
        }

        setPagesCache(prev => ({
          ...prev,
          [pageIdx]: {
            uploads: fetchedUploads,
            nextCursor,
            hasMore: fetchedHasMore
          }
        }))

        if (fetchedUploads.length > 0) {
          const firstId = fetchedUploads[0].upload_id
          setSelectedUploadId(firstId)
          fetchUploadDetails(firstId)
        } else {
          setSelectedUploadId(null)
        }
      }
    } catch (error) {
      console.error("Error fetching uploads:", error)
    } finally {
      setIsLoadingUploads(false)
    }
  }

  // Load first page of uploads on mount
  useEffect(() => {
    fetchUploadsPage(0, null)
  }, [])

  useEffect(() => {
    if (activeSection === "overview") {
      fetchPlatformMetrics()
    }
  }, [activeSection])

  const renderContent = () => {
    switch (activeSection) {
      case "overview":
        return (
          <div className="space-y-10">
            {/* Header */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-red-500/20 bg-red-500/10 text-red-500 text-sm font-medium">
                🛠️ Operational Overview
              </div>
              <h1 className="text-4xl font-bold leading-tight text-foreground">
                Admin Control Panel
              </h1>
              <p className="text-muted-foreground text-lg max-w-3xl leading-relaxed">
                Monitor system metrics, active AI pipelines, database connections, and digital workflow streams in real-time.
              </p>
            </div>

            {/* Platform Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Card 1: Total Uploads */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">Total Uploads</p>
                    {isLoadingMetrics ? (
                      <div className="h-8 bg-muted rounded animate-pulse w-24 mt-2" />
                    ) : (
                      <h3 className="text-2xl font-bold text-foreground mt-2">{platformMetrics?.total_uploads ?? 0}</h3>
                    )}
                  </div>
                  <span className="p-2 bg-violet-500/10 text-violet-500 rounded-xl">
                    <FileSpreadsheet size={20} />
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  Provider: <span className="font-semibold text-foreground capitalize">{platformMetrics?.active_database_provider || dbProvider}</span>
                </p>
              </div>

              {/* Card 2: Total Dishes Processed */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">Dishes Processed</p>
                    {isLoadingMetrics ? (
                      <div className="h-8 bg-muted rounded animate-pulse w-24 mt-2" />
                    ) : (
                      <h3 className="text-2xl font-bold text-foreground mt-2">{platformMetrics?.total_dishes_processed ?? 0}</h3>
                    )}
                  </div>
                  <span className="p-2 bg-emerald-500/10 text-emerald-500 rounded-xl">
                    <Activity size={20} />
                  </span>
                </div>
              </div>

              {/* Card 3: Total Visual Audits */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between h-40">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">Visual Audits</p>
                    {isLoadingMetrics ? (
                      <div className="h-8 bg-muted rounded animate-pulse w-24 mt-2" />
                    ) : (
                      <h3 className="text-2xl font-bold text-foreground mt-2">{platformMetrics?.total_visual_audits ?? 0}</h3>
                    )}
                  </div>
                  <span className="p-2 bg-primary/10 text-primary rounded-xl">
                    <Layers size={20} />
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  Asset Status: <span className="text-primary font-semibold">Synced in GCS</span>
                </p>
              </div>
            </div>

            {/* Performance Monitoring Section */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-foreground mb-6 flex items-center gap-2">
                <Server size={18} className="text-primary" />
                Pipeline Telemetry & Runtime Configuration
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Column: Operational Activity */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Operational Activity</h4>
                  
                  {/* Latest Processed File */}
                  <div className="bg-muted/40 p-4 rounded-xl border border-border/50 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Latest Ingested File</span>
                      {isLoadingMetrics ? (
                        <div className="h-4 bg-muted rounded animate-pulse w-32" />
                      ) : (
                        <span className="text-foreground font-semibold font-mono truncate max-w-[200px]" title={platformMetrics?.latest_file_name || "None"}>
                          {platformMetrics?.latest_file_name || "None"}
                        </span>
                      )}
                    </div>
                    <div className="flex justify-between text-xs text-muted-foreground border-t border-border/30 pt-2">
                      <span>Status: <span className={`font-bold ${platformMetrics?.latest_upload_status?.toLowerCase() === "processed" ? "text-emerald-500" : "text-yellow-500"}`}>{platformMetrics?.latest_upload_status?.toUpperCase() || "NONE"}</span></span>
                      <span className="font-mono">{platformMetrics?.latest_upload_timestamp || "None"}</span>
                    </div>
                  </div>

                  {/* Persisted Visual Assets Progress */}
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-muted-foreground">Persisted Visual Assets</span>
                      {isLoadingMetrics ? (
                        <div className="h-4 bg-muted rounded animate-pulse w-16" />
                      ) : (
                        <span className="text-foreground font-semibold">
                          {platformMetrics?.persisted_visual_assets ?? 0} / {platformMetrics?.total_visual_audits ?? 0} Assets
                        </span>
                      )}
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full transition-all duration-500" 
                        style={{ 
                          width: `${platformMetrics?.total_visual_audits ? Math.min(100, Math.round(((platformMetrics.persisted_visual_assets || 0) / platformMetrics.total_visual_audits) * 100)) : 0}%` 
                        }} 
                      />
                    </div>
                  </div>

                  {/* Persisted Spreadsheet Uploads Progress */}
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-muted-foreground">Persisted Spreadsheet Uploads</span>
                      {isLoadingMetrics ? (
                        <div className="h-4 bg-muted rounded animate-pulse w-16" />
                      ) : (
                        <span className="text-foreground font-semibold">
                          {platformMetrics?.total_persisted_uploads ?? 0} / {platformMetrics?.total_uploads ?? 0} Ingested
                        </span>
                      )}
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-violet-500 rounded-full transition-all duration-500" 
                        style={{ 
                          width: `${platformMetrics?.total_uploads ? Math.min(100, Math.round(((platformMetrics.total_persisted_uploads || 0) / platformMetrics.total_uploads) * 100)) : 0}%` 
                        }} 
                      />
                    </div>
                  </div>
                </div>

                {/* Right Column: Runtime Configuration */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Runtime Configuration</h4>
                  
                  {/* Active Database Provider */}
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-muted-foreground">Active Database Provider</span>
                      <span className="text-foreground font-semibold capitalize">{platformMetrics?.active_database_provider || dbProvider}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: "100%" }} />
                    </div>
                  </div>

                  {/* Active Insights Model */}
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-muted-foreground">Active AI Insights Model</span>
                      <span className="text-foreground font-semibold font-mono text-xs">{platformMetrics?.current_ai_models?.insights_model || "gemini-2.5-flash"}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: "100%" }} />
                    </div>
                  </div>

                  {/* Active Vision Model */}
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-muted-foreground">Active AI Vision Model</span>
                      <span className="text-foreground font-semibold font-mono text-xs">{platformMetrics?.current_ai_models?.vision_model || "gemini-2.0-flash"}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: "100%" }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case "database":
        return (
          <div className="space-y-10">
            {/* Header */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-primary/20 bg-primary/10 text-primary text-sm font-medium">
                🗄️ Database Management
              </div>
              <h1 className="text-4xl font-bold leading-tight text-foreground">
                Database Provider Configuration
              </h1>
              <p className="text-muted-foreground text-lg max-w-3xl leading-relaxed">
                Connect your operational data storage provider. Shift between regional databases or scale metadata collections.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Selector Box */}
              <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <h3 className="text-lg font-bold text-foreground">Configure Database Provider</h3>
                
                <div className="space-y-2 relative">
                  <label className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Select Active Provider</label>
                  
                  {/* Custom Dropdown Trigger */}
                  <button 
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="w-full bg-muted border border-border rounded-xl px-4 py-3.5 flex justify-between items-center text-foreground font-semibold hover:border-primary/50 hover:scale-[1.01] active:scale-[0.99] transition-all duration-300"
                  >
                    <span className="capitalize">{dbProvider}</span>
                    <ChevronDown size={18} className="text-muted-foreground" />
                  </button>

                  {/* Dropdown Options */}
                  {isDropdownOpen && (
                    <div className="absolute top-[84px] left-0 w-full bg-card border border-border rounded-xl shadow-xl z-20 overflow-hidden divide-y divide-border">
                      {/* Firebase */}
                      <button 
                        onClick={() => {
                          setDbProvider("firebase")
                          setIsDropdownOpen(false)
                        }}
                        className="w-full text-left px-5 py-3.5 flex items-center justify-between hover:bg-muted text-foreground transition-colors"
                      >
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm">Firebase / Firestore</span>
                          <span className="text-xs text-muted-foreground mt-0.5">Production document store client</span>
                        </div>
                        {dbProvider === "firebase" && <Check size={16} className="text-primary" />}
                      </button>

                      {/* Supabase (Disabled) */}
                      <div className="w-full text-left px-5 py-3.5 flex items-center justify-between bg-muted/40 cursor-not-allowed opacity-50">
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-muted-foreground">Supabase</span>
                            <span className="px-2 py-0.5 text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 rounded-full uppercase tracking-wider">Coming Soon</span>
                          </div>
                          <span className="text-xs text-muted-foreground mt-0.5">Relational Postgres client (Next Stage)</span>
                        </div>
                      </div>

                      {/* PostgreSQL (Disabled) */}
                      <div className="w-full text-left px-5 py-3.5 flex items-center justify-between bg-muted/40 cursor-not-allowed opacity-50">
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-muted-foreground">PostgreSQL</span>
                            <span className="px-2 py-0.5 text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 rounded-full uppercase tracking-wider">Coming Soon</span>
                          </div>
                          <span className="text-xs text-muted-foreground mt-0.5">Enterprise Direct RDBMS Connection</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Save Configuration Button */}
                <div className="pt-2 flex flex-col gap-3">
                  <button
                    onClick={handleSaveConfig}
                    disabled={isSaving || dbProvider !== "firebase"}
                    className="w-full md:w-auto px-6 py-3 rounded-xl bg-primary hover:bg-primary/90 hover:scale-[1.03] hover:shadow-xl hover:shadow-primary/20 active:scale-95 text-primary-foreground font-semibold text-sm transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                  >
                    {isSaving ? "Saving Configuration..." : "Save Configuration"}
                  </button>

                  {saveStatus === "success" && (
                    <div className="flex items-center gap-2 text-emerald-500 text-sm font-semibold bg-emerald-500/10 border border-emerald-500/20 p-3.5 rounded-xl transition-all animate-in fade-in slide-in-from-top-1 duration-200">
                      <CheckCircle2 size={16} className="shrink-0" />
                      <span>{statusMessage}</span>
                    </div>
                  )}

                  {saveStatus === "error" && (
                    <div className="flex items-center gap-2 text-red-500 text-sm font-semibold bg-red-500/10 border border-red-500/20 p-3.5 rounded-xl transition-all animate-in fade-in slide-in-from-top-1 duration-200">
                      <AlertCircle size={16} className="shrink-0" />
                      <span>{statusMessage}</span>
                    </div>
                  )}
                </div>

                <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl text-xs text-primary leading-relaxed flex gap-2 items-start">
                  <CheckCircle2 size={16} className="shrink-0 mt-0.5" />
                  <span>
                    Database provider adjustments are applied globally to the backend runtime. Shift between regional databases or scale metadata collections. Supabase & PostgreSQL require database initialization scripts inside your backend config folder.
                  </span>
                </div>
              </div>

              {/* Status Box */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <h3 className="text-lg font-bold text-foreground">Operational Status</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-1 border-b border-border">
                    <span className="text-sm text-muted-foreground">Connection State</span>
                    <span className="text-sm font-semibold text-emerald-500 flex items-center gap-1.5">
                      <CheckCircle2 size={14} /> Connected
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-border">
                    <span className="text-sm text-muted-foreground">Health Check</span>
                    <span className="text-xs text-foreground font-mono font-medium">Last run: 10s ago (Success)</span>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-border">
                    <span className="text-sm text-muted-foreground">SDK Network Latency</span>
                    <span className="text-sm font-semibold text-foreground font-mono">8ms</span>
                  </div>

                  <div className="flex items-center justify-between py-1">
                    <span className="text-sm text-muted-foreground">Private Media Bucket</span>
                    <span className="text-xs font-mono text-primary font-bold">menu-engineering</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case "ai-models":
        return (
          <div className="space-y-10">
            {/* Header */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-500 text-sm font-medium">
                🤖 AI Model Stack
              </div>
              <h1 className="text-4xl font-bold leading-tight text-foreground">
                Google Gemini Models Monitoring
              </h1>
              <p className="text-muted-foreground text-lg max-w-3xl leading-relaxed">
                Review Google GenAI APIs and active pipelines used to write content scripts, audit plating layouts, and compile video storyboards.
              </p>
            </div>

            {/* Models Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Card 1: AI Insights Model */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="w-10 h-10 bg-primary/10 text-primary rounded-xl flex items-center justify-center">
                    <Brain size={20} />
                  </div>
                  <h3 className="font-bold text-foreground">AI Insights Model</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Evaluates spreadsheet metrics, parses gross profit values, and generates the executive menu summary.
                  </p>
                </div>
                <div className="pt-4 border-t border-border space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Active Model</span>
                    <span className="font-mono text-foreground font-semibold">gemini-2.5-flash</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Temperature</span>
                    <span className="font-mono text-foreground font-semibold">0.2</span>
                  </div>
                </div>
              </div>

              {/* Card 2: Visual Intelligence Model */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="w-10 h-10 bg-blue-500/10 text-blue-500 rounded-xl flex items-center justify-center">
                    <BarChart3 size={20} />
                  </div>
                  <h3 className="font-bold text-foreground">Visual Intelligence Model</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Scores lighting, background details, plating alignment, and cross-references them with revenue.
                  </p>
                </div>
                <div className="pt-4 border-t border-border space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Active Model</span>
                    <span className="font-mono text-foreground font-semibold">gemini-2.0-flash</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Temperature</span>
                    <span className="font-mono text-foreground font-semibold">0.4</span>
                  </div>
                </div>
              </div>

              {/* Card 3: Video Generation Model */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="w-10 h-10 bg-violet-500/10 text-violet-500 rounded-xl flex items-center justify-center">
                    <Layers size={20} />
                  </div>
                  <h3 className="font-bold text-foreground">Video Generation Model</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Acts as the 10xFrame architect, creating luxury scripts and generating fully animated GSAP timeline HTML.
                  </p>
                </div>
                <div className="pt-4 border-t border-border space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Active Model</span>
                    <span className="font-mono text-foreground font-semibold">gemini-2.0-flash</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Temperature</span>
                    <span className="font-mono text-foreground font-semibold">0.5</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case "uploads":
        return (
          <div className="space-y-10">
            {/* Header */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-violet-500/20 bg-violet-500/10 text-violet-500 text-sm font-medium">
                📁 Data Ingestion Stream
              </div>
              <h1 className="text-4xl font-bold leading-tight text-foreground">
                Spreadsheet Upload Log
              </h1>
              <p className="text-muted-foreground text-lg max-w-3xl leading-relaxed">
                Explore the menu spreadsheets submitted for system analysis. Selecting a row displays structural details on the side panel.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Uploads Data Table */}
              <div className="lg:col-span-2 bg-card border border-border rounded-2xl shadow-sm overflow-hidden flex flex-col justify-between">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-muted/50 border-b border-border text-xs text-muted-foreground uppercase font-bold tracking-wider">
                      <th className="px-6 py-4">Filename</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {isLoadingUploads ? (
                      Array.from({ length: 5 }).map((_, idx) => (
                        <tr key={`skeleton-${idx}`} className="animate-pulse">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-muted rounded-lg" />
                              <div className="h-4 bg-muted rounded w-40" />
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="h-5 bg-muted rounded-full w-20" />
                          </td>
                          <td className="px-6 py-4">
                            <div className="h-4 bg-muted rounded w-24" />
                          </td>
                        </tr>
                      ))
                    ) : uploads.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-6 py-10 text-center text-sm text-muted-foreground">
                          No uploads ingested yet. Upload your first menu spreadsheet to get started!
                        </td>
                      </tr>
                    ) : (
                      uploads.map((upload) => (
                        <tr 
                          key={upload.upload_id} 
                          onClick={() => {
                            setSelectedUploadId(upload.upload_id)
                            fetchUploadDetails(upload.upload_id)
                          }}
                          className={`cursor-pointer transition-colors duration-200 text-sm ${
                            selectedUploadId === upload.upload_id 
                              ? "bg-primary/5 hover:bg-primary/10" 
                              : "hover:bg-muted"
                          }`}
                        >
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <span className="p-1.5 bg-primary/10 text-primary rounded-lg">
                                <FileSpreadsheet size={16} />
                              </span>
                              <span className="font-semibold text-foreground">{upload.file_name}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              upload.status.toLowerCase() === "processed" 
                                ? "bg-emerald-500/10 text-emerald-500" 
                                : "bg-yellow-500/10 text-yellow-500 animate-pulse"
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${
                                upload.status.toLowerCase() === "processed" ? "bg-emerald-500" : "bg-yellow-500"
                              }`} />
                              {upload.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                            {upload.uploaded_at}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                {/* Pagination Controls */}
                <div className="flex justify-between items-center px-6 py-4 bg-muted/30 border-t border-border mt-auto">
                  <button
                    onClick={() => {
                      if (pageIndex > 0) {
                        const newIdx = pageIndex - 1
                        setPageIndex(newIdx)
                        fetchUploadsPage(newIdx, pageCursors[newIdx])
                      }
                    }}
                    disabled={pageIndex === 0 || isLoadingUploads}
                    className="px-4 py-2 rounded-xl bg-card border border-border text-sm font-semibold text-foreground hover:bg-muted hover:scale-[1.03] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    Previous
                  </button>
                  <span className="text-xs text-muted-foreground font-mono">
                    Page {pageIndex + 1}
                  </span>
                  <button
                    onClick={() => {
                      if (hasMore) {
                        const newIdx = pageIndex + 1
                        setPageIndex(newIdx)
                        fetchUploadsPage(newIdx, pageCursors[newIdx])
                      }
                    }}
                    disabled={!hasMore || isLoadingUploads}
                    className="px-4 py-2 rounded-xl bg-card border border-border text-sm font-semibold text-foreground hover:bg-muted hover:scale-[1.03] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    Next
                  </button>
                </div>
              </div>

              {/* Visual Row Preview Side Panel */}
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm h-fit space-y-6">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <History size={18} className="text-primary" />
                  Asset Metadata
                </h3>

                {selectedUploadId ? (
                  isLoadingDetails && !detailsCache[selectedUploadId] ? (
                    <div className="py-10 text-center space-y-3">
                      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-sm text-muted-foreground font-medium animate-pulse">Loading asset details...</p>
                    </div>
                  ) : (() => {
                    const details = detailsCache[selectedUploadId];
                    const rowUpload = uploads.find(u => u.upload_id === selectedUploadId);
                    
                    const uploadId = selectedUploadId;
                    const fileName = details?.upload_metadata?.file_name || rowUpload?.file_name || "Unknown File";
                    const status = details?.processing_status || rowUpload?.status || "processed";
                    const uploadedAt = details?.upload_metadata?.uploaded_at || rowUpload?.uploaded_at || "";
                    const totalRevenue = details?.total_revenue !== undefined ? details.total_revenue : (rowUpload?.total_revenue || 0);
                    const dishCount = details?.dish_count !== undefined ? details.dish_count : (rowUpload?.dish_count || 0);
                    const cuisineCategory = details?.cuisine_category || rowUpload?.cuisine_category || "Uncategorized";
                    const visualAuditCount = details?.visual_audit_count !== undefined ? details.visual_audit_count : 0;
                    const aiInsightSummary = details?.ai_insight_summary || "Fetching summary insights...";

                    return (
                      <div className="space-y-5">
                        <div className="space-y-1">
                          <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">File Identifier</p>
                          <p className="text-sm font-semibold text-foreground font-mono break-all">{uploadId}</p>
                        </div>

                        <div className="space-y-1">
                          <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Target Filename</p>
                          <p className="text-sm font-semibold text-foreground break-all">{fileName}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Ingested Items</p>
                            <p className="text-lg font-bold text-foreground">{dishCount} Dishes</p>
                          </div>
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Estimated Revenue</p>
                            <p className="text-lg font-bold text-primary">₹{typeof totalRevenue === 'number' ? totalRevenue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : totalRevenue}</p>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Analyzed Cuisine Category</p>
                          <p className="text-sm font-semibold text-foreground">{cuisineCategory}</p>
                        </div>

                        <div className="space-y-1">
                          <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Indexing Timestamp</p>
                          <p className="text-xs font-mono text-muted-foreground flex items-center gap-1.5 mt-0.5">
                            <Clock size={12} /> {uploadedAt}
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Visual Audits</p>
                            <p className="text-sm font-semibold text-foreground">{visualAuditCount} Audits</p>
                          </div>
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Processing Status</p>
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                              status.toLowerCase() === "processed" 
                                ? "bg-emerald-500/10 text-emerald-500" 
                                : "bg-yellow-500/10 text-yellow-500 animate-pulse"
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${
                                status.toLowerCase() === "processed" ? "bg-emerald-500" : "bg-yellow-500"
                              }`} />
                              {status}
                            </span>
                          </div>
                        </div>

                        {details && (
                          <div className="space-y-1 border-t border-border pt-4">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-1">
                              <Brain size={14} className="text-primary" />
                              Executive Summary
                            </p>
                            <p className="text-xs text-muted-foreground leading-relaxed mt-1">{aiInsightSummary}</p>
                          </div>
                        )}

                        <div className="p-4 bg-muted border border-border rounded-xl flex items-start gap-2">
                          <span className="p-1 bg-primary/10 text-primary rounded-lg mt-0.5">
                            <CheckCircle2 size={12} />
                          </span>
                          <p className="text-[11px] text-muted-foreground leading-relaxed">
                            Upload metadata is fetched in real-time from the active database provider. Changing provider updates operational ingestion monitors.
                          </p>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <div className="text-center py-10 space-y-2">
                    <AlertCircle size={24} className="text-muted-foreground/30 mx-auto" />
                    <p className="text-sm text-muted-foreground/50">Select a spreadsheet log to preview metadata.</p>
                  </div>
                )}
            </div>
          </div>
        </div>
      )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-app-bg text-foreground transition-colors duration-300">
      <div className="flex">
        {/* Sticky Sidebar */}
        <div className="sticky top-0 h-screen shrink-0">
          <AdminSidebar 
            activeSection={activeSection} 
            setActiveSection={setActiveSection} 
          />
        </div>

        {/* Dynamic Content Area */}
        <div className="flex-1 px-10 py-10 overflow-x-hidden overflow-y-auto">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}
