import type {
  Stats, Competitor, Influencer, EventRow,
  Section, Region, ScrapeJobResponse, JobStatus,
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/api/stats`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchCompetitors(region?: Region, type?: string): Promise<Competitor[]> {
  const p = new URLSearchParams()
  if (region && region !== 'all') p.set('region', region)
  if (type && type !== 'all') p.set('type', type)
  const res = await fetch(`${BASE}/api/competitors?${p}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Competitors fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchInfluencers(region?: Region): Promise<Influencer[]> {
  const p = new URLSearchParams()
  if (region && region !== 'all') p.set('region', region)
  const res = await fetch(`${BASE}/api/influencers?${p}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Influencers fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchEvents(region?: Region): Promise<EventRow[]> {
  const p = new URLSearchParams()
  if (region && region !== 'all') p.set('region', region)
  const res = await fetch(`${BASE}/api/events?${p}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Events fetch failed: ${res.status}`)
  return res.json()
}

export async function startScrape(section: Section): Promise<ScrapeJobResponse> {
  const res = await fetch(`${BASE}/api/scrape/${section}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Scrape start failed: ${res.status}`)
  return res.json()
}

export async function startTopicScrape(topic: string): Promise<ScrapeJobResponse> {
  const p = new URLSearchParams({ topic })
  const res = await fetch(`${BASE}/api/scrape/events/topic?${p}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Topic scrape start failed: ${res.status}`)
  return res.json()
}

export async function pollJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${BASE}/api/scrape/status/${jobId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`)
  return res.json()
}
