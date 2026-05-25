'use client'
import { useEffect, useState, useRef } from 'react'
import DataTable, { Column } from '@/components/DataTable'
import RegionFilter from '@/components/RegionFilter'
import ScrapeButton from '@/components/ScrapeButton'
import { fetchEvents, startTopicScrape, pollJobStatus } from '@/lib/api'
import type { EventRow, Region } from '@/lib/types'

const COLUMNS: Column<EventRow>[] = [
  {
    key: 'name',
    label: 'Event',
    render: (r) => r.website
      ? <a href={r.website} target="_blank" rel="noreferrer" className="font-medium text-violet-300 hover:underline">{r.name}</a>
      : <span className="font-medium text-white">{r.name}</span>,
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
  const [search, setSearch] = useState('')
  const [showPast, setShowPast] = useState(false)
  const [topicState, setTopicState] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [topicMsg, setTopicMsg] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = () => {
    fetchEvents(region, !showPast).then(setData).catch(console.error)
  }

  useEffect(() => { load() }, [region, showPast])
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const today = new Date().toISOString().slice(0, 10)
  const filtered = search.trim()
    ? data.filter(e => {
        const q = search.toLowerCase()
        return (
          e.name?.toLowerCase().includes(q) ||
          e.description?.toLowerCase().includes(q) ||
          e.event_type?.toLowerCase().includes(q) ||
          e.location?.toLowerCase().includes(q) ||
          e.organizer?.toLowerCase().includes(q)
        )
      })
    : data

  const handleTopicScrape = async () => {
    const topic = search.trim()
    if (!topic) return
    setTopicState('running')
    setTopicMsg(`Searching '${topic}' events...`)
    try {
      const { job_id } = await startTopicScrape(topic)
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollJobStatus(job_id)
          setTopicMsg(status.message)
          if (status.status === 'done') {
            clearInterval(pollRef.current!)
            setTopicState('done')
            load()
            setTimeout(() => { setTopicState('idle'); setTopicMsg('') }, 8000)
          } else if (status.status === 'error') {
            clearInterval(pollRef.current!)
            setTopicState('error')
            setTimeout(() => { setTopicState('idle'); setTopicMsg('') }, 8000)
          }
        } catch {
          clearInterval(pollRef.current!)
          setTopicState('error')
          setTopicMsg('Polling failed')
          setTimeout(() => { setTopicState('idle'); setTopicMsg('') }, 8000)
        }
      }, 3000)
    } catch {
      setTopicState('error')
      setTopicMsg('Failed to start')
      setTimeout(() => { setTopicState('idle'); setTopicMsg('') }, 8000)
    }
  }

  const pastCount = data.filter(e => e.start_date && e.start_date < today).length

  const topicBtnClass = {
    idle: 'bg-violet-600 hover:bg-violet-700',
    running: 'bg-slate-600 cursor-not-allowed',
    done: 'bg-green-700',
    error: 'bg-red-700',
  }[topicState]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Events</h1>
          <p className="text-slate-400 text-sm mt-1">
            {filtered.length} {showPast ? 'total' : 'upcoming'} events
            {showPast && pastCount > 0 && <span className="text-slate-600 ml-2">({pastCount} past)</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPast(p => !p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              showPast
                ? 'bg-slate-700 border-slate-500 text-white'
                : 'bg-transparent border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            {showPast ? 'Showing all' : 'Show past'}
          </button>
          <ScrapeButton section="events" onDone={load} />
        </div>
      </div>

      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <RegionFilter value={region} onChange={setRegion} />
        <div className="flex items-center gap-2 ml-auto">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && topicState === 'idle' && search.trim() && handleTopicScrape()}
            placeholder="footwear, perfume, fashion…"
            className="bg-slate-800 border border-slate-700 text-sm text-white rounded-lg px-3 py-2 w-56 focus:outline-none focus:border-violet-500"
          />
          {topicState === 'running' && topicMsg && (
            <span className="text-slate-400 text-xs truncate max-w-[180px]">{topicMsg}</span>
          )}
          <button
            onClick={handleTopicScrape}
            disabled={!search.trim() || topicState === 'running'}
            className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2 ${topicBtnClass} disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {topicState === 'running' && (
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            {topicState === 'idle' ? 'Scrape Topic' : topicState === 'running' ? 'Scraping…' : topicState === 'done' ? 'Done ✓' : 'Failed'}
          </button>
        </div>
      </div>

      <DataTable columns={COLUMNS} data={filtered} />
    </div>
  )
}
