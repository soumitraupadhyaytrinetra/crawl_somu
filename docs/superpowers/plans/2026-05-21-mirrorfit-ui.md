# MirrorFit Intelligence UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend + Next.js 14 dashboard to view and trigger scrapes for competitors, influencers, and events.

**Architecture:** FastAPI on :8000 reads the existing SQLite DB via `storage/db.py` and triggers scrapes by spawning `python main.py --run-now --only-{section}` as a subprocess. Next.js on :3000 calls the FastAPI endpoints from client components.

**Tech Stack:** Python 3.13, FastAPI, uvicorn, Next.js 14 App Router, TypeScript, TailwindCSS

---

## File Map

**New files — backend:**
- `api/requirements.txt` — fastapi, uvicorn, python-dotenv
- `api/main.py` — all FastAPI endpoints + scrape job management

**New files — frontend:**
- `ui/` — scaffolded by `create-next-app`
- `ui/lib/types.ts` — TypeScript types for all API responses
- `ui/lib/api.ts` — typed fetch helpers for every endpoint
- `ui/components/NavSidebar.tsx` — left sidebar navigation
- `ui/components/StatsCard.tsx` — stat count card
- `ui/components/DataTable.tsx` — generic striped table
- `ui/components/ScrapeButton.tsx` — button with polling + status
- `ui/components/RegionFilter.tsx` — pill filter for all/india/uae/global
- `ui/app/layout.tsx` — root layout with sidebar
- `ui/app/globals.css` — base dark styles
- `ui/app/page.tsx` — dashboard with 4 stats cards
- `ui/app/competitors/page.tsx` — competitors table + filters
- `ui/app/influencers/page.tsx` — influencers table + filter
- `ui/app/events/page.tsx` — events table + filter

---

## Task 1: FastAPI Backend

**Files:**
- Create: `api/requirements.txt`
- Create: `api/main.py`

- [ ] **Step 1: Create `api/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Create `api/main.py`**

```python
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"
sys.path.insert(0, str(PROJECT_ROOT))

from storage.db import Database

app = FastAPI(title="MirrorFit Intelligence API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = PROJECT_ROOT / "data" / "competitors.db"
_jobs: dict[str, dict] = {}


def _db() -> Database:
    return Database(str(DB_PATH))


@app.get("/api/stats")
async def get_stats():
    db = _db()
    await db.init()
    competitors = await db.fetch_all()
    influencers = await db.fetch_all_influencers()
    events = await db.fetch_all_events(upcoming_only=True)
    last_scraped = None
    if competitors:
        timestamps = [c.get("scraped_at") for c in competitors if c.get("scraped_at")]
        if timestamps:
            last_scraped = max(timestamps)
    return {
        "competitors": len(competitors),
        "influencers": len(influencers),
        "events": len(events),
        "last_scraped": last_scraped,
    }


@app.get("/api/competitors")
async def get_competitors(region: Optional[str] = None, type: Optional[str] = None):
    db = _db()
    await db.init()
    rows = await db.fetch_all()
    if region:
        rows = [r for r in rows if r.get("region") == region]
    if type:
        rows = [r for r in rows if r.get("type") == type]
    return rows


@app.get("/api/influencers")
async def get_influencers(region: Optional[str] = None):
    db = _db()
    await db.init()
    rows = await db.fetch_all_influencers()
    if region:
        rows = [r for r in rows if r.get("region") == region]
    return rows


@app.get("/api/events")
async def get_events(region: Optional[str] = None):
    db = _db()
    await db.init()
    rows = await db.fetch_all_events(upcoming_only=True)
    if region:
        rows = [r for r in rows if r.get("region") == region]
    return rows


async def _run_scrape(section: str, job_id: str) -> None:
    _jobs[job_id] = {"status": "running", "message": f"Scraping {section}..."}
    flag = f"--only-{section}"
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(MAIN_PY), "--run-now", flag,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            _jobs[job_id] = {"status": "done", "message": f"{section.capitalize()} scraped successfully"}
        else:
            err = stderr.decode(errors="replace")[-500:]
            _jobs[job_id] = {"status": "error", "message": err}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "message": str(e)}


@app.post("/api/scrape/{section}")
async def start_scrape(section: str):
    if section not in ("competitors", "influencers", "events"):
        return {"error": "Invalid section. Use competitors, influencers, or events."}
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "message": f"Starting {section} scrape..."}
    asyncio.create_task(_run_scrape(section, job_id))
    return {"job_id": job_id}


@app.get("/api/scrape/status/{job_id}")
async def scrape_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return {"status": "not_found", "message": "Job not found"}
    return job
```

- [ ] **Step 3: Smoke-test the API**

Open a terminal in `crawlscraping/`:
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open browser at `http://localhost:8000/api/stats`. Expected: JSON with competitor/influencer/event counts.

- [ ] **Step 4: Commit**

```bash
git add api/
git commit -m "feat: add FastAPI backend for MirrorFit intelligence dashboard"
```

---

## Task 2: Scaffold Next.js App

**Files:**
- Create: `ui/` (via create-next-app)

- [ ] **Step 1: Scaffold the app**

Run from `crawlscraping/` root (PowerShell):
```powershell
npx create-next-app@14 ui --typescript --tailwind --app --no-src-dir --import-alias "@/*" --eslint --use-npm
```

When prompted interactively, accept all defaults. This creates `ui/` with Next.js 14, TypeScript, Tailwind, App Router.

- [ ] **Step 2: Remove boilerplate**

Delete the default content — replace `ui/app/page.tsx` and `ui/app/globals.css` with minimal stubs (will be replaced in later tasks):

```bash
# In ui/ directory
npm run dev
```

Verify: browser at `http://localhost:3000` shows the default Next.js page (we'll replace it).

Stop the dev server (`Ctrl+C`).

- [ ] **Step 3: Commit scaffold**

```bash
git add ui/
git commit -m "feat: scaffold Next.js 14 app for MirrorFit UI"
```

---

## Task 3: Types and API Helpers

**Files:**
- Create: `ui/lib/types.ts`
- Create: `ui/lib/api.ts`

- [ ] **Step 1: Create `ui/lib/types.ts`**

```typescript
export interface Stats {
  competitors: number
  influencers: number
  events: number
  last_scraped: string | null
}

export interface Competitor {
  id: number
  name: string
  display_name: string | null
  url: string | null
  region: string | null
  type: string | null
  scraped_at: string | null
  scraped_date: string | null
  tagline: string | null
  about: string | null
  pricing_plans: string | null
  has_virtual_tryon: number
  tryon_description: string | null
  tech_hints: string | null
  categories: string | null
  sample_products: string | null
  social_links: string | null
  has_newsletter: number
  ad_tech: string | null
}

export interface Influencer {
  id: number
  handle: string
  name: string | null
  platform: string
  followers: number | null
  niche: string | null
  region: string | null
  bio: string | null
  engagement_rate: string | null
  profile_url: string | null
  scraped_at: string | null
  scraped_date: string | null
  source_url: string | null
}

export interface EventRow {
  id: number
  name: string
  event_type: string | null
  location: string | null
  region: string | null
  start_date: string | null
  end_date: string | null
  website: string | null
  organizer: string | null
  description: string | null
  target_audience: string | null
  scraped_at: string | null
  scraped_date: string | null
  source_url: string | null
}

export type Section = 'competitors' | 'influencers' | 'events'
export type Region = 'all' | 'india' | 'uae' | 'global'

export interface ScrapeJobResponse {
  job_id: string
}

export interface JobStatus {
  status: 'running' | 'done' | 'error' | 'not_found'
  message: string
}
```

- [ ] **Step 2: Create `ui/lib/api.ts`**

```typescript
import type {
  Stats, Competitor, Influencer, EventRow,
  Section, Region, ScrapeJobResponse, JobStatus,
} from './types'

const BASE = 'http://localhost:8000'

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

export async function pollJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${BASE}/api/scrape/status/${jobId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`)
  return res.json()
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/lib/
git commit -m "feat: add TypeScript types and API fetch helpers"
```

---

## Task 4: Shared Components

**Files:**
- Create: `ui/components/NavSidebar.tsx`
- Create: `ui/components/StatsCard.tsx`
- Create: `ui/components/DataTable.tsx`
- Create: `ui/components/ScrapeButton.tsx`
- Create: `ui/components/RegionFilter.tsx`

- [ ] **Step 1: Create `ui/components/NavSidebar.tsx`**

```tsx
'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/competitors', label: 'Competitors' },
  { href: '/influencers', label: 'Influencers' },
  { href: '/events', label: 'Events' },
]

export default function NavSidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-52 min-h-screen bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="text-violet-400 font-bold text-lg leading-tight">MirrorFit</div>
        <div className="text-slate-500 text-xs tracking-widest uppercase mt-0.5">Intelligence</div>
      </div>
      <nav className="flex-1 py-3">
        {LINKS.map(({ href, label }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center px-5 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-violet-600/20 text-violet-300 border-r-2 border-violet-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: Create `ui/components/StatsCard.tsx`**

```tsx
import Link from 'next/link'

interface Props {
  label: string
  value: string | number
  href?: string
  sub?: string
}

export default function StatsCard({ label, value, href, sub }: Props) {
  const inner = (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-violet-500/60 transition-colors cursor-default">
      <div className="text-slate-400 text-sm mb-1">{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </div>
  )
  return href ? <Link href={href} className="block">{inner}</Link> : inner
}
```

- [ ] **Step 3: Create `ui/components/DataTable.tsx`**

```tsx
import React from 'react'

export interface Column<T> {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
}

interface Props<T extends { id?: number }> {
  columns: Column<T>[]
  data: T[]
}

export default function DataTable<T extends { id?: number }>({ columns, data }: Props<T>) {
  if (data.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-12 text-center border border-slate-700 rounded-lg">
        No data found
      </div>
    )
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-700">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left font-medium text-slate-300 whitespace-nowrap"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={row.id ?? i}
              className={`border-t border-slate-700 hover:bg-violet-600/10 transition-colors ${
                i % 2 === 0 ? 'bg-slate-900' : 'bg-slate-800'
              }`}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className="px-4 py-2.5 text-slate-300 max-w-xs"
                >
                  {col.render
                    ? col.render(row)
                    : <span className="truncate block">{String((row as Record<string, unknown>)[col.key] ?? '—')}</span>
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 4: Create `ui/components/ScrapeButton.tsx`**

```tsx
'use client'
import { useState, useEffect, useRef } from 'react'
import { startScrape, pollJobStatus } from '@/lib/api'
import type { Section } from '@/lib/types'

type State = 'idle' | 'running' | 'done' | 'error'

interface Props {
  section: Section
  onDone?: () => void
}

export default function ScrapeButton({ section, onDone }: Props) {
  const [state, setState] = useState<State>('idle')
  const [message, setMessage] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const handleClick = async () => {
    setState('running')
    setMessage('Starting...')
    try {
      const { job_id } = await startScrape(section)
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollJobStatus(job_id)
          setMessage(status.message)
          if (status.status === 'done') {
            clearInterval(pollRef.current!)
            setState('done')
            onDone?.()
            setTimeout(() => { setState('idle'); setMessage('') }, 10000)
          } else if (status.status === 'error') {
            clearInterval(pollRef.current!)
            setState('error')
            setTimeout(() => { setState('idle'); setMessage('') }, 10000)
          }
        } catch {
          clearInterval(pollRef.current!)
          setState('error')
          setMessage('Polling failed')
          setTimeout(() => { setState('idle'); setMessage('') }, 10000)
        }
      }, 3000)
    } catch {
      setState('error')
      setMessage('Failed to start scrape')
      setTimeout(() => { setState('idle'); setMessage('') }, 10000)
    }
  }

  const label = {
    idle: `Scrape ${section.charAt(0).toUpperCase() + section.slice(1)}`,
    running: 'Scraping...',
    done: 'Done ✓',
    error: 'Failed',
  }[state]

  const btnClass = {
    idle: 'bg-violet-600 hover:bg-violet-700',
    running: 'bg-slate-600 cursor-not-allowed',
    done: 'bg-green-700',
    error: 'bg-red-700',
  }[state]

  return (
    <div className="flex items-center gap-3">
      {state === 'running' && message && (
        <span className="text-slate-400 text-sm truncate max-w-xs">{message}</span>
      )}
      <button
        onClick={handleClick}
        disabled={state === 'running'}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors ${btnClass}`}
      >
        {state === 'running' && (
          <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {label}
      </button>
    </div>
  )
}
```

- [ ] **Step 5: Create `ui/components/RegionFilter.tsx`**

```tsx
'use client'
import type { Region } from '@/lib/types'

const REGIONS: { value: Region; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'india', label: 'India' },
  { value: 'uae', label: 'UAE' },
  { value: 'global', label: 'Global' },
]

interface Props {
  value: Region
  onChange: (r: Region) => void
}

export default function RegionFilter({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {REGIONS.map(({ value: v, label }) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            value === v
              ? 'bg-violet-600 text-white'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-600'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add ui/components/
git commit -m "feat: add shared UI components (NavSidebar, StatsCard, DataTable, ScrapeButton, RegionFilter)"
```

---

## Task 5: Root Layout and Global Styles

**Files:**
- Modify: `ui/app/globals.css`
- Modify: `ui/app/layout.tsx`

- [ ] **Step 1: Replace `ui/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body {
  background-color: rgb(2 6 23); /* slate-950 */
  color: white;
}
```

- [ ] **Step 2: Replace `ui/app/layout.tsx`**

```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import NavSidebar from '@/components/NavSidebar'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MirrorFit Intelligence',
  description: 'Competitive intelligence dashboard for MirrorFit AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-950 text-white flex min-h-screen`}>
        <NavSidebar />
        <main className="flex-1 p-8 overflow-auto min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add ui/app/globals.css ui/app/layout.tsx
git commit -m "feat: configure root layout with dark theme and sidebar"
```

---

## Task 6: Dashboard Page

**Files:**
- Modify: `ui/app/page.tsx`

- [ ] **Step 1: Replace `ui/app/page.tsx`**

```tsx
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

  const lastScraped = stats?.last_scraped
    ? new Date(stats.last_scraped).toLocaleString()
    : '—'

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
          sub="Instagram, Apify"
        />
        <StatsCard
          label="Upcoming Events"
          value={stats ? stats.events : '…'}
          href="/events"
          sub="India · UAE · Global"
        />
        <StatsCard
          label="Last Scraped"
          value={stats ? lastScraped : '…'}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify dashboard loads**

Start both servers (two terminals):
```bash
# Terminal 1
cd api && uvicorn main:app --reload --port 8000

# Terminal 2
cd ui && npm run dev
```

Open `http://localhost:3000`. Expected: dark page with 4 stat cards showing counts.

- [ ] **Step 3: Commit**

```bash
git add ui/app/page.tsx
git commit -m "feat: add dashboard page with stats cards"
```

---

## Task 7: Competitors Page

**Files:**
- Create: `ui/app/competitors/page.tsx`

- [ ] **Step 1: Create `ui/app/competitors/page.tsx`**

```tsx
'use client'
import { useEffect, useState } from 'react'
import DataTable, { Column } from '@/components/DataTable'
import RegionFilter from '@/components/RegionFilter'
import ScrapeButton from '@/components/ScrapeButton'
import { fetchCompetitors } from '@/lib/api'
import type { Competitor, Region } from '@/lib/types'

type TypeFilter = 'all' | 'platform' | 'retailer'

const COLUMNS: Column<Competitor>[] = [
  {
    key: 'display_name',
    label: 'Name',
    render: (r) => (
      <div>
        <div className="font-medium text-white">{r.display_name || r.name}</div>
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

  const load = () => {
    fetchCompetitors(region, typeFilter !== 'all' ? typeFilter : undefined).then(setData).catch(console.error)
  }

  useEffect(() => { load() }, [region, typeFilter])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Competitors</h1>
          <p className="text-slate-400 text-sm mt-1">{data.length} results</p>
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
      </div>

      <DataTable columns={COLUMNS} data={data} />
    </div>
  )
}
```

- [ ] **Step 2: Verify competitors page**

Open `http://localhost:3000/competitors`. Expected: table with ~94 rows, region + type filters work, scrape button visible.

- [ ] **Step 3: Commit**

```bash
git add ui/app/competitors/
git commit -m "feat: add competitors page with region/type filters"
```

---

## Task 8: Influencers Page

**Files:**
- Create: `ui/app/influencers/page.tsx`

- [ ] **Step 1: Create `ui/app/influencers/page.tsx`**

```tsx
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
```

- [ ] **Step 2: Verify influencers page**

Open `http://localhost:3000/influencers`. Expected: ~128 rows sorted by followers, region filter works, handles link to Instagram.

- [ ] **Step 3: Commit**

```bash
git add ui/app/influencers/
git commit -m "feat: add influencers page with follower counts and Instagram links"
```

---

## Task 9: Events Page

**Files:**
- Create: `ui/app/events/page.tsx`

- [ ] **Step 1: Create `ui/app/events/page.tsx`**

```tsx
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
    render: (r) => (
      <span className="font-medium text-white">{r.name}</span>
    ),
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
```

- [ ] **Step 2: Verify events page**

Open `http://localhost:3000/events`. Expected: upcoming events table, dates shown in violet, TBC for null dates, region filter works.

- [ ] **Step 3: Commit**

```bash
git add ui/app/events/
git commit -m "feat: add events page with upcoming filter and region pills"
```

---

## Task 10: Final Smoke Test

- [ ] **Step 1: Start both servers**

Terminal 1 (from `crawlscraping/`):
```bash
cd api
uvicorn main:app --reload --port 8000
```

Terminal 2 (from `crawlscraping/`):
```bash
cd ui
npm run dev
```

- [ ] **Step 2: Verify all pages**

| URL | Expected |
|-----|----------|
| `http://localhost:3000/` | 4 stat cards with real counts |
| `http://localhost:3000/competitors` | Table with ~94 rows, filters work |
| `http://localhost:3000/influencers` | Table with ~128 rows, @handles link |
| `http://localhost:3000/events` | Upcoming events, dates in violet |

- [ ] **Step 3: Test a scrape button**

On the Events page, click **Scrape Events**. Expected: button shows spinner + "Scraping...", after ~2-5 min shows "Done ✓", table refreshes.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete MirrorFit Intelligence UI (FastAPI + Next.js dashboard)"
```
