import json
import os
from datetime import datetime
from pathlib import Path

import aiosqlite

from scrapers.models import CompetitorData

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    UNIQUE(name, scraped_date)
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_region ON competitors(region)",
    "CREATE INDEX IF NOT EXISTS idx_type ON competitors(type)",
    "CREATE INDEX IF NOT EXISTS idx_scraped_date ON competitors(scraped_date)",
]


class Database:
    def __init__(self, db_path: str = "./data/competitors.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(CREATE_TABLE)
            for idx in CREATE_INDEXES:
                await conn.execute(idx)
            await conn.commit()

    async def upsert(self, record: CompetitorData):
        scraped_at = record.scraped_at or datetime.utcnow()
        scraped_date = scraped_at.date().isoformat()
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO competitors
                    (name, display_name, url, region, type, scraped_at, scraped_date,
                     tagline, about, pricing_plans, has_virtual_tryon, tryon_description,
                     tech_hints, categories, sample_products)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(name, scraped_date) DO UPDATE SET
                    display_name=excluded.display_name,
                    url=excluded.url,
                    scraped_at=excluded.scraped_at,
                    tagline=excluded.tagline,
                    about=excluded.about,
                    pricing_plans=excluded.pricing_plans,
                    has_virtual_tryon=excluded.has_virtual_tryon,
                    tryon_description=excluded.tryon_description,
                    tech_hints=excluded.tech_hints,
                    categories=excluded.categories,
                    sample_products=excluded.sample_products
                """,
                (
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
                ),
            )
            await conn.commit()

    async def fetch_all(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM competitors ORDER BY scraped_at DESC")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def fetch_by_region(self, region: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM competitors WHERE region=? ORDER BY scraped_at DESC",
                (region,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
