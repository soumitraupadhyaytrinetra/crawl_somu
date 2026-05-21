'use client'
import { useEffect, useState } from 'react'
import DataTable, { Column } from '@/components/DataTable'
import RegionFilter from '@/components/RegionFilter'
import ScrapeButton from '@/components/ScrapeButton'
import { fetchEvents } from '@/lib/api'
import type { EventRow, Region } from '@/lib/types'

const COLUMNS: Column<EventRow>[] = [
  {
    key: 'name',
    label: 'Event',
    render: (r) => <span className="font-medium text-white">{r.name}</span>,
  },
  {
    key: 'start_date',
    label: 'Date',
    render: (r) => r.start_date
      ? <span className="font-mono text-sm text-violet-300">{r.start_date}</span>
      : <span className="text-slate-500 text-xs">TBC</span>,
  },
  { key: 'end_date', label: 'End', render: (r) => r.end_date ?? '—' },
  { key: 'location', label: 'Location', render: (r) => r.location ?? '—' },
  { key: 'region', label: 'Region', render: (r) => r.region?.toUpperCase() ?? '—' },
  { key: 'event_type', label: 'Type', render: (r) => r.event_type ?? '—' },
  { key: 'organizer', label: 'Organizer', render: (r) => r.organizer ?? '—' },
  {
    key: 'website',
    label: 'Link',
    render: (r) => r.website
      ? <a href={r.website} target="_blank" rel="noreferrer" className="text-violet-400 hover:underline text-xs">Visit ↗</a>
      : '—',
  },
]

export default function EventsPage() {
  const [data, setData] = useState<EventRow[]>([])
  const [region, setRegion] = useState<Region>('all')

  const load = () => {
    fetchEvents(region).then(setData).catch(console.error)
  }

  useEffect(() => { load() }, [region])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Events</h1>
          <p className="text-slate-400 text-sm mt-1">{data.length} upcoming events</p>
        </div>
        <ScrapeButton section="events" onDone={load} />
      </div>

      <div className="mb-5">
        <RegionFilter value={region} onChange={setRegion} />
      </div>

      <DataTable columns={COLUMNS} data={data} />
    </div>
  )
}
