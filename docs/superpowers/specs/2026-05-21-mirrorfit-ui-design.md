# MirrorFit Intelligence — UI Design Spec
**Date:** 2026-05-21  
**Status:** Approved

---

## Overview

Web dashboard for the MirrorFit Intelligence Scraper. Displays scraped competitors, influencers, and events from the existing SQLite database. Allows users to trigger scrapes per section via buttons. Internal tool — no auth required.

---

## Architecture

```
crawlscraping/
├── api/                        ← FastAPI backend (NEW)
│   ├── main.py                 ← all endpoints
│   └── requirements.txt        ← fastapi, uvicorn
├── ui/                         ← Next.js 14 frontend (NEW)
│   ├── app/
│   │   ├── layout.tsx          ← root layout + nav
│   │   ├── page.tsx            ← dashboard (stats)
│   │   ├── competitors/
│   │   │   └── page.tsx
│   │   ├── influencers/
│   │   │   └── page.tsx
│   │   └── events/
│   │       └── page.tsx
│   ├── components/
│   │   ├── NavSidebar.tsx
│   │   ├── StatsCard.tsx
│   │   ├── DataTable.tsx       ← reusable table
│   │   ├── ScrapeButton.tsx    ← button + spinner + status
│   │   └── RegionFilter.tsx
│   ├── lib/
│   │   └── api.ts              ← typed fetch helpers
│   ├── tailwind.config.ts
│   └── package.json
├── scrapers/                   ← unchanged
├── storage/                    ← unchanged
└── main.py                     ← unchanged
```

---

## FastAPI Backend (`api/main.py`)

**Port:** 8000  
**CORS:** allow `http://localhost:3000`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats` | Total counts: competitors, influencers, events + last_scraped timestamp |
| GET | `/api/competitors` | All competitors. Query params: `region`, `type` |
| GET | `/api/influencers` | All influencers. Query params: `region` |
| GET | `/api/events` | Upcoming events. Query params: `region` |
| POST | `/api/scrape/competitors` | Start competitors scrape in background |
| POST | `/api/scrape/influencers` | Start influencers scrape in background |
| POST | `/api/scrape/events` | Start events scrape in background |
| GET | `/api/scrape/status/{job_id}` | Poll scrape job status |

### Scrape Job Flow
1. POST `/api/scrape/{section}` → creates `asyncio.Task`, returns `{"job_id": "<uuid>"}` immediately
2. Job state stored in in-memory dict: `{job_id: {status: "running"|"done"|"error", message: str}}`
3. Frontend polls `/api/scrape/status/{job_id}` every 3 seconds
4. On "done" or "error": frontend stops polling, shows result

### Data Layer
Reuses existing `storage/db.py` — `Database` class with `fetch_all()`, `fetch_all_influencers()`, `fetch_all_events()`.

---

## Next.js Frontend (`ui/`)

**Port:** 3000  
**Stack:** Next.js 14 App Router, TailwindCSS, TypeScript

### Pages

#### Dashboard (`/`)
- 4 stats cards: Competitors (total), Influencers (total), Events (upcoming), Last Scraped
- Cards link to respective section pages

#### Competitors (`/competitors`)
- Filter bar: Region (all/india/uae/global) + Type (all/platform/retailer)
- Table columns: Name, Region, Type, Has Virtual Try-On, Pricing Plans, Tech Hints, URL
- `[Scrape Competitors]` button top-right

#### Influencers (`/influencers`)
- Filter bar: Region (all/india/uae/global)
- Table columns: Handle, Name, Followers, Niche, Region, Bio
- Default sort: followers descending
- `[Scrape Influencers]` button top-right

#### Events (`/events`)
- Filter bar: Region (all/india/uae/global)
- Table columns: Name, Date, End Date, Location, Region, Type, Organizer
- Default: upcoming only (start_date >= today or null)
- `[Scrape Events]` button top-right

### Shared Components

**NavSidebar** — left sidebar, 200px wide. Links: Dashboard, Competitors, Influencers, Events. MirrorFit logo/name at top.

**ScrapeButton** — props: `section: "competitors"|"influencers"|"events"`. States: idle → loading (spinner + "Scraping…") → done ("Done ✓") → error ("Failed"). Disabled during scrape. Auto-resets to idle after 10s.

**DataTable** — generic sortable table. Props: `columns`, `data`. Striped rows, hover highlight.

**RegionFilter** — pill buttons: All / India / UAE / Global.

### Visual Style
- **Theme:** Dark (slate-900 background, slate-800 cards)
- **Accent:** Violet/purple (`violet-500` / `violet-600`)
- **Font:** Inter
- **Tables:** slate-700 header, alternating slate-800/slate-900 rows, violet hover
- **Buttons:** `bg-violet-600 hover:bg-violet-700`, white text

---

## Running Locally

```bash
# Terminal 1 — FastAPI
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Next.js
cd ui
npm install
npm run dev
```

---

## Out of Scope
- Authentication / login
- Real-time scrape log streaming (poll-based status is sufficient)
- Mobile responsive design
- Deployment / Docker
