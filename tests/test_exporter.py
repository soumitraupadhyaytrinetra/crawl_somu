import asyncio
import json
import os
import csv
import pytest
from datetime import datetime
from scrapers.models import CompetitorData
from storage.db import Database
from storage.exporter import Exporter

TEST_DB = "./data/test_export.db"
TEST_OUTPUT = "./output/test"

@pytest.fixture(autouse=True)
def cleanup():
    yield
    for f in [TEST_DB]:
        if os.path.exists(f):
            os.remove(f)
    import shutil
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)

@pytest.mark.asyncio
async def test_export_csv_creates_file():
    db = Database(TEST_DB)
    await db.init()
    await db.upsert(CompetitorData(
        name="myntra", display_name="Myntra",
        url="https://myntra.com", region="india", type="retailer",
        scraped_at=datetime.utcnow(), tagline="Fashion brand",
    ))
    exporter = Exporter(db, output_dir=TEST_OUTPUT)
    path = await exporter.export_csv()
    assert os.path.exists(path)
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "myntra"

@pytest.mark.asyncio
async def test_export_json_grouped():
    db = Database(TEST_DB)
    await db.init()
    await db.upsert(CompetitorData(
        name="myntra", display_name="Myntra",
        url="https://myntra.com", region="india", type="retailer",
        scraped_at=datetime.utcnow(),
    ))
    await db.upsert(CompetitorData(
        name="vue_ai", display_name="Vue.ai",
        url="https://vue.ai", region="global", type="platform",
        scraped_at=datetime.utcnow(),
    ))
    exporter = Exporter(db, output_dir=TEST_OUTPUT)
    path = await exporter.export_json()
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert "india" in data
    assert "global" in data
    assert data["india"]["retailer"][0]["name"] == "myntra"
    assert data["global"]["platform"][0]["name"] == "vue_ai"
