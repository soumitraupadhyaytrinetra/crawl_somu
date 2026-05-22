import json
import os
from datetime import datetime, date

import asyncpg

from scrapers.models import CompetitorData, EventData, InfluencerData

CREATE_COMPETITORS = """
CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT,
    url TEXT,
    region TEXT,
    type TEXT,
    scraped_at TEXT,
    scraped_date TEXT,
    tagline TEXT,
    about TEXT,
    pricing_plans TEXT,
    has_virtual_tryon INTEGER DEFAULT 0,
    tryon_description TEXT,
    tech_hints TEXT,
    categories TEXT,
    sample_products TEXT,
    social_links TEXT,
    has_newsletter INTEGER DEFAULT 0,
    ad_tech TEXT,
    UNIQUE(name, scraped_date)
)
"""

CREATE_INFLUENCERS = """
CREATE TABLE IF NOT EXISTS influencers (
    id SERIAL PRIMARY KEY,
    handle TEXT NOT NULL,
    name TEXT,
    platform TEXT DEFAULT 'instagram',
    followers INTEGER,
    niche TEXT,
    region TEXT,
    bio TEXT,
    engagement_rate TEXT,
    profile_url TEXT,
    scraped_at TEXT,
    scraped_date TEXT,
    source_url TEXT,
    UNIQUE(handle, scraped_date)
)
"""

CREATE_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    event_type TEXT,
    location TEXT,
    region TEXT,
    start_date TEXT,
    end_date TEXT,
    website TEXT,
    organizer TEXT,
    description TEXT,
    target_audience TEXT,
    scraped_at TEXT,
    scraped_date TEXT,
    source_url TEXT,
    UNIQUE(name, scraped_date)
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_region ON competitors(region)",
    "CREATE INDEX IF NOT EXISTS idx_type ON competitors(type)",
    "CREATE INDEX IF NOT EXISTS idx_scraped_date ON competitors(scraped_date)",
    "CREATE INDEX IF NOT EXISTS idx_inf_region ON influencers(region)",
    "CREATE INDEX IF NOT EXISTS idx_inf_platform ON influencers(platform)",
    "CREATE INDEX IF NOT EXISTS idx_evt_region ON events(region)",
]

_MIGRATE_COMPETITORS = [
    "ALTER TABLE competitors ADD COLUMN IF NOT EXISTS social_links TEXT",
    "ALTER TABLE competitors ADD COLUMN IF NOT EXISTS has_newsletter INTEGER DEFAULT 0",
    "ALTER TABLE competitors ADD COLUMN IF NOT EXISTS ad_tech TEXT",
]


class Database:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._pool = None

    async def init(self):
        db_url = self.db_url.replace("postgres://", "postgresql://", 1)
        self._pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_COMPETITORS)
            await conn.execute(CREATE_INFLUENCERS)
            await conn.execute(CREATE_EVENTS)
            for idx in CREATE_INDEXES:
                await conn.execute(idx)
            for stmt in _MIGRATE_COMPETITORS:
                try:
                    await conn.execute(stmt)
                except Exception:
                    pass

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def upsert(self, record: CompetitorData):
        scraped_at = record.scraped_at or datetime.utcnow()
        scraped_date = scraped_at.date().isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO competitors
                    (name, display_name, url, region, type, scraped_at, scraped_date,
                     tagline, about, pricing_plans, has_virtual_tryon, tryon_description,
                     tech_hints, categories, sample_products,
                     social_links, has_newsletter, ad_tech)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
                ON CONFLICT(name, scraped_date) DO UPDATE SET
                    display_name=EXCLUDED.display_name,
                    url=EXCLUDED.url,
                    scraped_at=EXCLUDED.scraped_at,
                    tagline=EXCLUDED.tagline,
                    about=EXCLUDED.about,
                    pricing_plans=EXCLUDED.pricing_plans,
                    has_virtual_tryon=EXCLUDED.has_virtual_tryon,
                    tryon_description=EXCLUDED.tryon_description,
                    tech_hints=EXCLUDED.tech_hints,
                    categories=EXCLUDED.categories,
                    sample_products=EXCLUDED.sample_products,
                    social_links=EXCLUDED.social_links,
                    has_newsletter=EXCLUDED.has_newsletter,
                    ad_tech=EXCLUDED.ad_tech
                """,
                record.name,
                record.display_name,
                record.url,
                record.region,
                record.type,
                scraped_at.isoformat(),
                scraped_date,
                record.tagline,
                record.about,
                json.dumps(record.pricing_plans),
                int(record.has_virtual_tryon),
                record.tryon_description,
                json.dumps(record.tech_hints),
                json.dumps(record.categories),
                json.dumps([p.model_dump() for p in record.sample_products]),
                json.dumps(record.social_links),
                int(record.has_newsletter),
                json.dumps(record.ad_tech),
            )

    async def upsert_influencer(self, record: InfluencerData):
        scraped_at = record.scraped_at or datetime.utcnow()
        scraped_date = scraped_at.date().isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO influencers
                    (handle, name, platform, followers, niche, region, bio,
                     engagement_rate, profile_url, scraped_at, scraped_date, source_url)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT(handle, scraped_date) DO UPDATE SET
                    name=EXCLUDED.name,
                    followers=EXCLUDED.followers,
                    niche=EXCLUDED.niche,
                    bio=EXCLUDED.bio,
                    engagement_rate=EXCLUDED.engagement_rate,
                    profile_url=EXCLUDED.profile_url,
                    scraped_at=EXCLUDED.scraped_at,
                    source_url=EXCLUDED.source_url
                """,
                record.handle,
                record.name,
                record.platform,
                record.followers,
                json.dumps(record.niche),
                record.region,
                record.bio,
                record.engagement_rate,
                record.profile_url,
                scraped_at.isoformat(),
                scraped_date,
                record.source_url,
            )

    async def upsert_event(self, record: EventData):
        scraped_at = record.scraped_at or datetime.utcnow()
        scraped_date = scraped_at.date().isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events
                    (name, event_type, location, region, start_date, end_date,
                     website, organizer, description, target_audience,
                     scraped_at, scraped_date, source_url)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                ON CONFLICT(name, scraped_date) DO UPDATE SET
                    event_type=EXCLUDED.event_type,
                    location=EXCLUDED.location,
                    start_date=EXCLUDED.start_date,
                    end_date=EXCLUDED.end_date,
                    website=EXCLUDED.website,
                    organizer=EXCLUDED.organizer,
                    description=EXCLUDED.description,
                    target_audience=EXCLUDED.target_audience,
                    scraped_at=EXCLUDED.scraped_at,
                    source_url=EXCLUDED.source_url
                """,
                record.name,
                record.event_type,
                record.location,
                record.region,
                record.start_date,
                record.end_date,
                record.website,
                record.organizer,
                record.description,
                json.dumps(record.target_audience),
                scraped_at.isoformat(),
                scraped_date,
                record.source_url,
            )

    async def fetch_all(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM competitors ORDER BY scraped_at DESC")
            return [dict(r) for r in rows]

    async def fetch_by_region(self, region: str) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM competitors WHERE region=$1 ORDER BY scraped_at DESC",
                region,
            )
            return [dict(r) for r in rows]

    async def fetch_all_influencers(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM influencers ORDER BY followers DESC NULLS LAST"
            )
            return [dict(r) for r in rows]

    async def fetch_apify_influencers(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM influencers WHERE source_url='apify:instagram-scraper' ORDER BY followers DESC NULLS LAST"
            )
            return [dict(r) for r in rows]

    async def clear_influencers(self):
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM influencers")

    async def fetch_all_events(self, upcoming_only: bool = True) -> list[dict]:
        async with self._pool.acquire() as conn:
            if upcoming_only:
                today = date.today().isoformat()
                rows = await conn.fetch(
                    "SELECT * FROM events WHERE start_date IS NULL OR start_date >= $1 ORDER BY start_date",
                    today,
                )
            else:
                rows = await conn.fetch("SELECT * FROM events ORDER BY region, start_date")
            return [dict(r) for r in rows]
