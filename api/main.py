import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"
sys.path.insert(0, str(PROJECT_ROOT))

from storage.db import Database

_db_instance: Database = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_instance
    db_url = os.environ.get("DATABASE_URL", "postgresql://localhost/mirrorfit")
    _db_instance = Database(db_url)
    await _db_instance.init()
    yield
    await _db_instance.close()


app = FastAPI(title="MirrorFit Intelligence API", lifespan=lifespan)

_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict] = {}


@app.get("/api/stats")
async def get_stats():
    competitors = await _db_instance.fetch_all()
    influencers = await _db_instance.fetch_all_influencers()
    events = await _db_instance.fetch_all_events(upcoming_only=True)
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
async def get_competitors(region: Optional[str] = None, competitor_type: Optional[str] = Query(None, alias="type")):
    rows = await _db_instance.fetch_all()
    if region:
        rows = [r for r in rows if r.get("region") == region]
    if competitor_type:
        rows = [r for r in rows if r.get("type") == competitor_type]
    return rows


@app.get("/api/influencers")
async def get_influencers(region: Optional[str] = None):
    rows = await _db_instance.fetch_all_influencers()
    if region:
        rows = [r for r in rows if r.get("region") == region]
    return rows


@app.get("/api/events")
async def get_events(region: Optional[str] = None):
    rows = await _db_instance.fetch_all_events(upcoming_only=True)
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
        try:
            _stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            _jobs[job_id] = {"status": "error", "message": "Scrape timed out after 5 minutes"}
            asyncio.get_event_loop().call_later(60, _jobs.pop, job_id, None)
            return
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


@app.post("/api/scrape/events/topic")
async def start_topic_scrape(topic: str = Query(...)):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "message": f"Searching '{topic}' events..."}
    asyncio.create_task(_run_topic_scrape(topic, job_id))
    return {"job_id": job_id}


async def _run_topic_scrape(topic: str, job_id: str) -> None:
    _jobs[job_id] = {"status": "running", "message": f"Scraping '{topic}' events..."}
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(MAIN_PY), "--run-now", "--only-events", "--topic-events", topic,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            _jobs[job_id] = {"status": "error", "message": "Topic scrape timed out"}
            asyncio.get_event_loop().call_later(60, _jobs.pop, job_id, None)
            return
        if proc.returncode == 0:
            _jobs[job_id] = {"status": "done", "message": f"'{topic}' events scraped"}
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
