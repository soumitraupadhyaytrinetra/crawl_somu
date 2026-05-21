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
async def get_competitors(region: Optional[str] = None, competitor_type: Optional[str] = None):
    db = _db()
    await db.init()
    rows = await db.fetch_all()
    if region:
        rows = [r for r in rows if r.get("region") == region]
    if competitor_type:
        rows = [r for r in rows if r.get("type") == competitor_type]
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
            asyncio.get_event_loop().call_later(60, _jobs.pop, job_id, None)
        else:
            err = stderr.decode(errors="replace")[-500:]
            _jobs[job_id] = {"status": "error", "message": err}
            asyncio.get_event_loop().call_later(60, _jobs.pop, job_id, None)
    except Exception as e:
        _jobs[job_id] = {"status": "error", "message": str(e)}
        asyncio.get_event_loop().call_later(60, _jobs.pop, job_id, None)


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
