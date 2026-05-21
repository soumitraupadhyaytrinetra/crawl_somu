'use client'
import { useEffect, useState } from 'react'
import DataTable, { Column } from '@/components/DataTable'
import RegionFilter from '@/components/RegionFilter'
import ScrapeButton from '@/components/ScrapeButton'
import { fetchInfluencers } from '@/lib/api'
import type { Influencer, Region } from '@/lib/types'

const COLUMNS: Column<Influencer>[] = [
  {
    key: 'handle',
    label: 'Handle',
    render: (r) => (
      <a
        href={r.profile_url ?? `https://instagram.com/${r.handle}`}
        target="_blank"
        rel="noreferrer"
        className="text-violet-400 hover:underline font-medium"
      >
        @{r.handle}
      </a>
    ),
  },
  { key: 'name', label: 'Name', render: (r) => r.name ?? '—' },
  {
    key: 'followers',
    label: 'Followers',
    render: (r) => r.followers
      ? <span className="font-mono text-sm">{r.followers.toLocaleString()}</span>
      : '—',
  },
  {
    key: 'niche',
    label: 'Niche',
    render: (r) => {
      try {
        const n: string[] = JSON.parse(r.niche ?? '[]')
        return n.length > 0
          ? <span className="text-xs text-slate-300">{n.join(', ')}</span>
          : '—'
      } catch { return r.niche ?? '—' }
    },
  },
  { key: 'region', label: 'Region', render: (r) => r.region?.toUpperCase() ?? '—' },
  {
    key: 'bio',
    label: 'Bio',
    render: (r) => (
      <span className="text-slate-400 text-xs">{r.bio?.slice(0, 80) ?? '—'}</span>
    ),
  },
]

export default function InfluencersPage() {
  const [data, setData] = useState<Influencer[]>([])
  const [region, setRegion] = useState<Region>('all')

  const load = () => {
    fetchInfluencers(region).then(setData).catch(console.error)
  }

  useEffect(() => { load() }, [region])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Influencers</h1>
          <p className="text-slate-400 text-sm mt-1">{data.length} results · sorted by followers</p>
        </div>
        <ScrapeButton section="influencers" onDone={load} />
      </div>

      <div className="mb-5">
        <RegionFilter value={region} onChange={setRegion} />
      </div>

      <DataTable columns={COLUMNS} data={data} />
    </div>
  )
}
