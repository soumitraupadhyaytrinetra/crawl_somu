'use client'
import { useEffect, useState } from 'react'
import StatsCard from '@/components/StatsCard'
import { fetchStats } from '@/lib/api'
import type { Stats } from '@/lib/types'

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetchStats().then(setStats).catch(() => setError(true))
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
      <p className="text-slate-400 text-sm mb-6">MirrorFit competitive intelligence overview</p>

      {error && (
        <div className="mb-6 p-4 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm">
          ⚠ Cannot connect to API at <code className="font-mono">localhost:8000</code>.
          Run: <code className="font-mono">cd api && uvicorn main:app --reload --port 8000</code>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatsCard
          label="Competitors"
          value={stats ? stats.competitors : '…'}
          href="/competitors"
          sub="Click to view"
        />
        <StatsCard
          label="Influencers"
          value={stats ? stats.influencers : '…'}
          href="/influencers"
          sub="Click to view"
        />
        <StatsCard
          label="Upcoming Events"
          value={stats ? stats.events : '…'}
          href="/events"
          sub="Click to view"
        />
      </div>
    </div>
  )
}
