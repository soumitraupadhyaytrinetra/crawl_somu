import asyncio
import pytest
import os
from datetime import datetime, date
from scrapers.models import CompetitorData, SampleProduct
from storage.db import Database

TEST_DB = "./data/test_competitors.db"

@pytest.fixture(autouse=True)
def cleanup():
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.mark.asyncio
async def test_create_schema():
    db = Database(TEST_DB)
    await db.init()
    # No error = schema created

@pytest.mark.asyncio
async def test_upsert_and_fetch():
    db = Database(TEST_DB)
    await db.init()
    record = CompetitorData(
        name="myntra",
        display_name="Myntra",
        url="https://www.myntra.com",
        region="india",
        type="retailer",
        scraped_at=datetime.utcnow(),
        tagline="Fashion and you",
        has_virtual_tryon=True,
        tech_hints=["AR", "AI"],
        categories=["Men", "Women"],
        sample_products=[SampleProduct(name="T-Shirt", price=499.0, currency="INR")],
    )
    await db.upsert(record)
    rows = await db.fetch_all()
    assert len(rows) == 1
    assert rows[0]["name"] == "myntra"
    assert rows[0]["has_virtual_tryon"] == 1

@pytest.mark.asyncio
async def test_upsert_same_day_overwrites():
    db = Database(TEST_DB)
    await db.init()
    base = dict(
        name="myntra", display_name="Myntra",
        url="https://www.myntra.com", region="india",
        type="retailer", scraped_at=datetime.utcnow(),
    )
    await db.upsert(CompetitorData(**base, tagline="First"))
    await db.upsert(CompetitorData(**base, tagline="Second"))
    rows = await db.fetch_all()
    assert len(rows) == 1
    assert rows[0]["tagline"] == "Second"

@pytest.mark.asyncio
async def test_fetch_by_region():
    db = Database(TEST_DB)
    await db.init()
    await db.upsert(CompetitorData(
        name="myntra", display_name="Myntra",
        url="https://myntra.com", region="india", type="retailer",
        scraped_at=datetime.utcnow(),
    ))
    await db.upsert(CompetitorData(
        name="namshi", display_name="Namshi",
        url="https://namshi.com", region="uae", type="retailer",
        scraped_at=datetime.utcnow(),
    ))
    india = await db.fetch_by_region("india")
    assert len(india) == 1
    assert india[0]["name"] == "myntra"
