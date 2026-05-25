'use client'
import { useEffect, useState } from 'react'
import DataTable, { Column } from '@/components/DataTable'
import RegionFilter from '@/components/RegionFilter'
import ScrapeButton from '@/components/ScrapeButton'
import { fetchCompetitors } from '@/lib/api'
import type { Competitor, Region } from '@/lib/types'

type TypeFilter = 'all' | 'platform' | 'retailer'

function safeJson(s: string | null): string[] {
  try { return JSON.parse(s ?? '[]') } catch { return [] }
}

const COLUMNS: Column<Competitor>[] = [
  {
    key: 'display_name',
    label: 'Name',
    render: (r) => (
      <div>
        {r.url
          ? <a href={r.url} target="_blank" rel="noreferrer" className="font-medium text-violet-300 hover:underline">{r.display_name || r.name}</a>
          : <div className="font-medium text-white">{r.display_name || r.name}</div>
        }
        {r.tagline && <div className="text-xs text-slate-500 truncate max-w-[200px]">{r.tagline}</div>}
      </div>
    ),
  },
  { key: 'region', label: 'Region', render: (r) => r.region?.toUpperCase() ?? '—' },
  { key: 'type', label: 'Type', render: (r) => r.type ?? '—' },
  {
    key: 'has_virtual_tryon',
    label: 'Try-On',
    render: (r) => r.has_virtual_tryon
      ? <span className="text-green-400 font-medium">✓</span>
      : <span className="text-slate-600">—</span>,
  },
  {
    key: 'pricing_plans',
    label: 'Pricing',
    render: (r) => {
      try {
        const plans: string[] = JSON.parse(r.pricing_plans ?? '[]')
        return plans.length > 0
          ? <span className="text-xs">{plans.slice(0, 2).join(', ')}</span>
          : '—'
      } catch { return '—' }
    },
  },
  {
    key: 'tech_hints',
    label: 'Tech',
    render: (r) => {
      try {
        const hints: string[] = JSON.parse(r.tech_hints ?? '[]')
        return hints.length > 0
          ? <span className="text-xs text-slate-400">{hints.slice(0, 3).join(', ')}</span>
          : '—'
      } catch { return '—' }
    },
  },
  {
    key: 'url',
    label: 'URL',
    render: (r) => r.url
      ? <a href={r.url} target="_blank" rel="noreferrer" className="text-violet-400 hover:underline text-xs truncate block max-w-[180px]">{r.url.replace(/^https?:\/\//, '')}</a>
      : '—',
  },
]

export default function CompetitorsPage() {
  const [data, setData] = useState<Competitor[]>([])
  const [region, setRegion] = useState<Region>('all')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [search, setSearch] = useState('')

  const load = () => {
    fetchCompetitors(region, typeFilter !== 'all' ? typeFilter : undefined).then(setData).catch(console.error)
  }

  useEffect(() => { load() }, [region, typeFilter])

  const filtered = search.trim()
    ? data.filter(c => {
        const q = search.toLowerCase()
        return (
          c.name?.toLowerCase().includes(q) ||
          c.display_name?.toLowerCase().includes(q) ||
          c.tagline?.toLowerCase().includes(q) ||
          c.about?.toLowerCase().includes(q) ||
          c.url?.toLowerCase().includes(q) ||
          safeJson(c.tech_hints).some(t => t.toLowerCase().includes(q)) ||
          safeJson(c.categories).some(t => t.toLowerCase().includes(q))
        )
      })
    : data

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Competitors</h1>
          <p className="text-slate-400 text-sm mt-1">{filtered.length} results</p>
        </div>
        <ScrapeButton section="competitors" onDone={load} />
      </div>

      <div className="flex flex-wrap gap-4 mb-5 items-center">
        <RegionFilter value={region} onChange={setRegion} />
        <div className="h-5 border-l border-slate-700" />
        <div className="flex gap-2">
          {(['all', 'platform', 'retailer'] as TypeFilter[]).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-colors ${
                typeFilter === t
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-600'
              }`}
            >
              {t === 'all' ? 'All Types' : t}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search name, tech, category…"
          className="ml-auto bg-slate-800 border border-slate-700 text-sm text-white rounded-lg px-3 py-2 w-56 focus:outline-none focus:border-violet-500"
        />
      </div>

      <DataTable columns={COLUMNS} data={filtered} />
    </div>
  )
}
