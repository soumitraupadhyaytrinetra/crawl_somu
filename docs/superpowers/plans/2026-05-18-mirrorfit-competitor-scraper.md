# MirrorFit Competitor Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular crawl4ai-based scraper that collects competitive intelligence (products, business info, try-on features) from AI try-on platforms and fashion retailers across India, UAE, and globally — storing results in SQLite with CSV+JSON exports and a configurable cron schedule.

**Architecture:** Central `competitors.yaml` drives all targets; two scraper classes (platform, retailer) inherit from a shared crawl4ai base; storage layer writes to SQLite and exports CSV+JSON; APScheduler reads cron expression from `.env`; `main.py` CLI ties everything together.

**Tech Stack:** Python 3.11+, crawl4ai 0.4+, APScheduler 3.10+, aiosqlite 0.19+, pydantic 2+, python-dotenv, pyyaml, pandas 2+

---

## File Map

| File | Responsibility |
|------|---------------|
| `.env` | Runtime config: schedule, paths, concurrency |
| `config/competitors.yaml` | All target competitors with URLs and regions |
| `scrapers/base_scraper.py` | crawl4ai wrapper, retry, delay, extraction |
| `scrapers/platform_scraper.py` | AI try-on platform scraping logic |
| `scrapers/retailer_scraper.py` | Fashion retailer scraping logic |
| `scrapers/models.py` | Pydantic models for scraped data |
| `storage/db.py` | SQLite schema creation, upsert, query |
| `storage/exporter.py` | CSV + JSON export from SQLite |
| `scheduler/scheduler.py` | APScheduler cron daemon |
| `main.py` | CLI entry point |
| `tests/fixtures/sample_platform.html` | Static HTML fixture for platform tests |
| `tests/fixtures/sample_retailer.html` | Static HTML fixture for retailer tests |
| `tests/test_models.py` | Pydantic model validation tests |
| `tests/test_storage.py` | SQLite write/read/upsert tests |
| `tests/test_exporter.py` | CSV + JSON output format tests |
| `tests/test_base_scraper.py` | Extraction logic tests with fixtures |

---

## Task 1: Project Scaffolding + Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `.env.example`
- Create: `config/__init__.py`
- Create: `scrapers/__init__.py`
- Create: `storage/__init__.py`
- Create: `scheduler/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/` (directory)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p config scrapers storage scheduler tests/fixtures output data docs/superpowers/plans
```

- [ ] **Step 2: Create requirements.txt**

```
crawl4ai>=0.4.0
apscheduler>=3.10.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
aiosqlite>=0.19.0
pandas>=2.0.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 3: Create .env**

```env
SCRAPE_SCHEDULE=0 2 * * *
OUTPUT_DIR=./output
DB_PATH=./data/competitors.db
MAX_CONCURRENCY=5
LOG_LEVEL=INFO
USER_AGENT=Mozilla/5.0 (compatible; MirrorFitBot/1.0)
REQUEST_DELAY_MS=1500
```

- [ ] **Step 4: Create .env.example** (same content as .env — safe to commit)

```env
SCRAPE_SCHEDULE=0 2 * * *
OUTPUT_DIR=./output
DB_PATH=./data/competitors.db
MAX_CONCURRENCY=5
LOG_LEVEL=INFO
USER_AGENT=Mozilla/5.0 (compatible; MirrorFitBot/1.0)
REQUEST_DELAY_MS=1500
```

- [ ] **Step 5: Create all `__init__.py` files**

Each file is empty:
```python
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .env.example config/__init__.py scrapers/__init__.py storage/__init__.py scheduler/__init__.py tests/__init__.py
git commit -m "chore: project scaffold and dependencies"
```

---

## Task 2: Competitor Config (competitors.yaml)

**Files:**
- Create: `config/competitors.yaml`

- [ ] **Step 1: Create competitors.yaml**

```yaml
competitors:
  # AI Try-On Platforms — Global
  - name: vue_ai
    display_name: "Vue.ai"
    url: "https://vue.ai"
    region: global
    type: platform
    scrape_paths:
      - /
      - /platform
      - /pricing

  - name: zakeke
    display_name: "Zakeke"
    url: "https://www.zakeke.com"
    region: global
    type: platform
    scrape_paths:
      - /
      - /pricing

  - name: fit_match
    display_name: "Fit:Match"
    url: "https://www.fitmatch.ai"
    region: global
    type: platform
    scrape_paths:
      - /

  - name: sizer_me
    display_name: "Sizer.me"
    url: "https://sizer.me"
    region: global
    type: platform
    scrape_paths:
      - /

  - name: threedlook
    display_name: "3DLOOK"
    url: "https://3dlook.ai"
    region: global
    type: platform
    scrape_paths:
      - /
      - /pricing

  # Fashion Retailers — India
  - name: myntra
    display_name: "Myntra"
    url: "https://www.myntra.com"
    region: india
    type: retailer
    scrape_paths:
      - /
      - /men
      - /women

  - name: nykaa_fashion
    display_name: "Nykaa Fashion"
    url: "https://www.nykaafashion.com"
    region: india
    type: retailer
    scrape_paths:
      - /
      - /women
      - /men

  - name: ajio
    display_name: "Ajio"
    url: "https://www.ajio.com"
    region: india
    type: retailer
    scrape_paths:
      - /
      - /s/men
      - /s/women

  - name: flipkart_fashion
    display_name: "Flipkart Fashion"
    url: "https://www.flipkart.com"
    region: india
    type: retailer
    scrape_paths:
      - /clothing-and-accessories

  - name: meesho
    display_name: "Meesho"
    url: "https://meesho.com"
    region: india
    type: retailer
    scrape_paths:
      - /

  - name: tata_cliq
    display_name: "Tata Cliq"
    url: "https://www.tatacliq.com"
    region: india
    type: retailer
    scrape_paths:
      - /
      - /men
      - /women

  # Fashion Retailers — UAE/Dubai
  - name: noon_fashion
    display_name: "Noon Fashion"
    url: "https://www.noon.com"
    region: uae
    type: retailer
    scrape_paths:
      - /uae-en/fashion

  - name: namshi
    display_name: "Namshi"
    url: "https://en-ae.namshi.com"
    region: uae
    type: retailer
    scrape_paths:
      - /
      - /men
      - /women

  - name: ounass
    display_name: "Ounass"
    url: "https://www.ounass.ae"
    region: uae
    type: retailer
    scrape_paths:
      - /
      - /women
      - /men

  - name: level_shoes
    display_name: "Level Shoes"
    url: "https://www.levelshoes.com"
    region: uae
    type: retailer
    scrape_paths:
      - /

  - name: sixth_street
    display_name: "6thStreet"
    url: "https://en-ae.6thstreet.com"
    region: uae
    type: retailer
    scrape_paths:
      - /

  - name: max_fashion
    display_name: "Max Fashion UAE"
    url: "https://www.maxfashion.com"
    region: uae
    type: retailer
    scrape_paths:
      - /ae
```

- [ ] **Step 2: Commit**

```bash
git add config/competitors.yaml
git commit -m "feat: add competitor targets config"
```

---

## Task 3: Pydantic Models

**Files:**
- Create: `scrapers/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

`tests/test_models.py`:
```python
import pytest
from scrapers.models import CompetitorData, SampleProduct

def test_competitor_data_required_fields():
    c = CompetitorData(
        name="test",
        display_name="Test",
        url="https://test.com",
        region="india",
        type="retailer",
    )
    assert c.name == "test"
    assert c.has_virtual_tryon is False
    assert c.tech_hints == []
    assert c.categories == []
    assert c.sample_products == []
    assert c.pricing_plans == []

def test_competitor_data_region_validation():
    with pytest.raises(Exception):
        CompetitorData(
            name="bad",
            display_name="Bad",
            url="https://bad.com",
            region="mars",
            type="retailer",
        )

def test_competitor_data_type_validation():
    with pytest.raises(Exception):
        CompetitorData(
            name="bad",
            display_name="Bad",
            url="https://bad.com",
            region="india",
            type="unknown",
        )

def test_sample_product_model():
    p = SampleProduct(name="T-Shirt", price=999.0, currency="INR", image_url="https://img.com/1.jpg")
    assert p.name == "T-Shirt"
    assert p.currency == "INR"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError: No module named 'scrapers.models'`

- [ ] **Step 3: Create scrapers/models.py**

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl


class SampleProduct(BaseModel):
    name: str
    price: float | None = None
    currency: str | None = None
    image_url: str | None = None


class CompetitorData(BaseModel):
    name: str
    display_name: str
    url: str
    region: Literal["india", "uae", "global"]
    type: Literal["platform", "retailer"]
    scraped_at: datetime | None = None

    tagline: str | None = None
    about: str | None = None
    pricing_plans: list[str] = []

    has_virtual_tryon: bool = False
    tryon_description: str | None = None
    tech_hints: list[str] = []

    categories: list[str] = []
    sample_products: list[SampleProduct] = []
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_models.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scrapers/models.py tests/test_models.py
git commit -m "feat: add pydantic models for competitor data"
```

---

## Task 4: SQLite Storage Layer

**Files:**
- Create: `storage/db.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests**

`tests/test_storage.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_storage.py -v
```

Expected: `ImportError: No module named 'storage.db'`

- [ ] **Step 3: Create storage/db.py**

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_storage.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add storage/db.py tests/test_storage.py
git commit -m "feat: add SQLite storage layer with upsert and region filter"
```

---

## Task 5: Exporter (CSV + JSON)

**Files:**
- Create: `storage/exporter.py`
- Create: `tests/test_exporter.py`

- [ ] **Step 1: Write failing tests**

`tests/test_exporter.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_exporter.py -v
```

Expected: `ImportError: No module named 'storage.exporter'`

- [ ] **Step 3: Create storage/exporter.py**

```python
import csv
import json
import os
from datetime import date
from pathlib import Path

from storage.db import Database


class Exporter:
    def __init__(self, db: Database, output_dir: str = "./output"):
        self.db = db
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    async def export_csv(self) -> str:
        rows = await self.db.fetch_all()
        filename = f"competitors_{date.today().isoformat()}.csv"
        path = os.path.join(self.output_dir, filename)
        if not rows:
            return path
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return path

    async def export_json(self) -> str:
        rows = await self.db.fetch_all()
        filename = f"competitors_{date.today().isoformat()}.json"
        path = os.path.join(self.output_dir, filename)
        grouped: dict = {}
        for row in rows:
            region = row.get("region", "unknown")
            ctype = row.get("type", "unknown")
            grouped.setdefault(region, {}).setdefault(ctype, []).append(row)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, indent=2, ensure_ascii=False)
        return path
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_exporter.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add storage/exporter.py tests/test_exporter.py
git commit -m "feat: add CSV and JSON exporter"
```

---

## Task 6: Base Scraper

**Files:**
- Create: `scrapers/base_scraper.py`
- Create: `tests/fixtures/sample_platform.html`
- Create: `tests/fixtures/sample_retailer.html`
- Create: `tests/test_base_scraper.py`

- [ ] **Step 1: Create HTML fixtures**

`tests/fixtures/sample_platform.html`:
```html
<!DOCTYPE html>
<html>
<head><title>VirtualFit AI - Virtual Try-On Platform</title>
<meta name="description" content="AI-powered virtual try-on for fashion retailers">
</head>
<body>
<h1>VirtualFit AI</h1>
<p class="tagline">Try before you buy with AI-powered virtual fitting rooms</p>
<section class="about">
  <p>VirtualFit AI uses 3D body scanning and augmented reality to let shoppers try on clothes virtually.</p>
</section>
<section class="features">
  <p>Our platform leverages AR, AI, LiDAR and 3D technology for accurate virtual try-on.</p>
</section>
<section class="pricing">
  <div class="plan">Starter - $99/month</div>
  <div class="plan">Professional - $299/month</div>
  <div class="plan">Enterprise - Contact us</div>
</section>
</body>
</html>
```

`tests/fixtures/sample_retailer.html`:
```html
<!DOCTYPE html>
<html>
<head><title>FashionStore - Shop Men and Women Clothing</title>
<meta name="description" content="India's leading fashion destination">
</head>
<body>
<h1>FashionStore</h1>
<p class="tagline">India's top fashion destination</p>
<nav class="categories">
  <a href="/men">Men</a>
  <a href="/women">Women</a>
  <a href="/kids">Kids</a>
  <a href="/accessories">Accessories</a>
</nav>
<section class="virtual-tryon">
  <p>Try our new AI-powered virtual try-on feature. See how clothes look on you before buying.</p>
</section>
<div class="product">
  <span class="name">Classic White T-Shirt</span>
  <span class="price">₹499</span>
  <img src="https://img.example.com/tshirt.jpg" alt="T-Shirt">
</div>
<div class="product">
  <span class="name">Blue Denim Jeans</span>
  <span class="price">₹1299</span>
  <img src="https://img.example.com/jeans.jpg" alt="Jeans">
</div>
</body>
</html>
```

- [ ] **Step 2: Write failing tests**

`tests/test_base_scraper.py`:
```python
import pytest
from scrapers.base_scraper import extract_tech_hints, extract_pricing_plans, detect_virtual_tryon

def test_extract_tech_hints_finds_keywords():
    text = "Our platform uses AR, AI, LiDAR and 3D technology for virtual try-on."
    hints = extract_tech_hints(text)
    assert "AR" in hints
    assert "AI" in hints
    assert "3D" in hints
    assert "LiDAR" in hints

def test_extract_tech_hints_no_duplicates():
    text = "AR technology with AR support and more AR features"
    hints = extract_tech_hints(text)
    assert hints.count("AR") == 1

def test_extract_pricing_plans():
    text = "Starter - $99/month\nProfessional - $299/month\nEnterprise - Contact us"
    plans = extract_pricing_plans(text)
    assert len(plans) == 3
    assert any("99" in p for p in plans)

def test_detect_virtual_tryon_true():
    text = "Try our AI-powered virtual try-on feature"
    assert detect_virtual_tryon(text) is True

def test_detect_virtual_tryon_false():
    text = "Shop the latest fashion trends online"
    assert detect_virtual_tryon(text) is False

def test_extract_tech_hints_empty_text():
    assert extract_tech_hints("") == []

def test_detect_virtual_tryon_ar_keyword():
    text = "Experience augmented reality shopping"
    assert detect_virtual_tryon(text) is True
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
pytest tests/test_base_scraper.py -v
```

Expected: `ImportError: No module named 'scrapers.base_scraper'`

- [ ] **Step 4: Create scrapers/base_scraper.py**

```python
import asyncio
import logging
import os
import re
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from dotenv import load_dotenv

from scrapers.models import CompetitorData, SampleProduct

load_dotenv()

logger = logging.getLogger(__name__)

TECH_KEYWORDS = [
    "AR", "AI", "3D", "LiDAR", "augmented reality", "machine learning",
    "computer vision", "virtual try-on", "body scan", "deep learning",
    "neural network", "pose estimation",
]

TRYON_KEYWORDS = [
    "virtual try-on", "virtual tryon", "try on", "augmented reality",
    "AR try", "virtual fitting", "try before you buy", "see how it looks",
    "virtual wardrobe",
]

PRICING_PATTERNS = [
    r"\$[\d,]+(?:\.\d+)?(?:/(?:mo|month|yr|year))?",
    r"(?:starter|basic|pro|professional|enterprise|free)\s*[-–]\s*[^\n]{3,50}",
    r"(?:plan|tier|package)\s*:?\s*[^\n]{3,50}",
]


def extract_tech_hints(text: str) -> list[str]:
    if not text:
        return []
    found = []
    text_lower = text.lower()
    for kw in TECH_KEYWORDS:
        if kw.lower() in text_lower and kw not in found:
            found.append(kw)
    return found


def extract_pricing_plans(text: str) -> list[str]:
    if not text:
        return []
    plans = []
    for pattern in PRICING_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            cleaned = m.strip()
            if cleaned and cleaned not in plans:
                plans.append(cleaned)
    return plans[:10]


def detect_virtual_tryon(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in TRYON_KEYWORDS)


class BaseScraper:
    def __init__(self):
        self.delay_ms = int(os.getenv("REQUEST_DELAY_MS", "1500"))
        self.user_agent = os.getenv(
            "USER_AGENT", "Mozilla/5.0 (compatible; MirrorFitBot/1.0)"
        )
        self.max_retries = 3

    async def fetch(self, url: str) -> str | None:
        config = CrawlerRunConfig(
            user_agent=self.user_agent,
            wait_for_timeout=5000,
        )
        for attempt in range(self.max_retries):
            try:
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url, config=config)
                    if result.success:
                        return result.markdown
                    logger.warning("Fetch failed %s attempt %d: %s", url, attempt + 1, result.error_message)
            except Exception as e:
                logger.warning("Exception fetching %s attempt %d: %s", url, attempt + 1, e)
            if attempt < self.max_retries - 1:
                backoff = (2 ** attempt) * (self.delay_ms / 1000)
                await asyncio.sleep(backoff)
        return None

    async def scrape(self, competitor: dict) -> CompetitorData | None:
        raise NotImplementedError
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_base_scraper.py -v
```

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add scrapers/base_scraper.py tests/test_base_scraper.py tests/fixtures/
git commit -m "feat: add base scraper with tech hint and try-on detection"
```

---

## Task 7: Platform Scraper

**Files:**
- Create: `scrapers/platform_scraper.py`

- [ ] **Step 1: Create scrapers/platform_scraper.py**

```python
import asyncio
import logging
from datetime import datetime

from scrapers.base_scraper import (
    BaseScraper,
    detect_virtual_tryon,
    extract_pricing_plans,
    extract_tech_hints,
)
from scrapers.models import CompetitorData

logger = logging.getLogger(__name__)


class PlatformScraper(BaseScraper):
    async def scrape(self, competitor: dict) -> CompetitorData | None:
        name = competitor["name"]
        base_url = competitor["url"]
        paths = competitor.get("scrape_paths", ["/"])

        combined_text = ""
        for path in paths:
            url = base_url.rstrip("/") + path
            logger.info("Scraping platform %s at %s", name, url)
            text = await self.fetch(url)
            if text:
                combined_text += "\n" + text
            await asyncio.sleep(self.delay_ms / 1000)

        if not combined_text.strip():
            logger.error("No content scraped for platform %s", name)
            return None

        tagline = _extract_first_line(combined_text, max_len=150)
        about = _extract_paragraph(combined_text, max_len=500)
        pricing_plans = extract_pricing_plans(combined_text)
        tech_hints = extract_tech_hints(combined_text)
        has_tryon = detect_virtual_tryon(combined_text)
        tryon_desc = _extract_tryon_sentence(combined_text)

        return CompetitorData(
            name=name,
            display_name=competitor.get("display_name", name),
            url=base_url,
            region=competitor["region"],
            type="platform",
            scraped_at=datetime.utcnow(),
            tagline=tagline,
            about=about,
            pricing_plans=pricing_plans,
            has_virtual_tryon=has_tryon,
            tryon_description=tryon_desc,
            tech_hints=tech_hints,
            categories=[],
            sample_products=[],
        )


def _extract_first_line(text: str, max_len: int = 150) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if len(stripped) > 10:
            return stripped[:max_len]
    return None


def _extract_paragraph(text: str, max_len: int = 500) -> str | None:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    return paragraphs[0][:max_len] if paragraphs else None


def _extract_tryon_sentence(text: str) -> str | None:
    tryon_kw = ["virtual try-on", "try on", "augmented reality", "virtual fitting"]
    for line in text.splitlines():
        line_lower = line.lower()
        if any(kw in line_lower for kw in tryon_kw):
            return line.strip()[:300]
    return None
```

- [ ] **Step 2: Verify import works**

```bash
python -c "from scrapers.platform_scraper import PlatformScraper; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scrapers/platform_scraper.py
git commit -m "feat: add platform scraper"
```

---

## Task 8: Retailer Scraper

**Files:**
- Create: `scrapers/retailer_scraper.py`

- [ ] **Step 1: Create scrapers/retailer_scraper.py**

```python
import asyncio
import logging
import re
from datetime import datetime

from scrapers.base_scraper import (
    BaseScraper,
    detect_virtual_tryon,
    extract_tech_hints,
)
from scrapers.models import CompetitorData, SampleProduct

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = [
    "men", "women", "kids", "accessories", "footwear", "ethnic",
    "western", "sportswear", "activewear", "bags", "jewellery",
    "beauty", "lingerie", "plus size",
]

CURRENCY_SYMBOLS = {
    "₹": "INR",
    "$": "USD",
    "AED": "AED",
    "د.إ": "AED",
    "£": "GBP",
    "€": "EUR",
}


class RetailerScraper(BaseScraper):
    async def scrape(self, competitor: dict) -> CompetitorData | None:
        name = competitor["name"]
        base_url = competitor["url"]
        paths = competitor.get("scrape_paths", ["/"])

        combined_text = ""
        for path in paths:
            url = base_url.rstrip("/") + path
            logger.info("Scraping retailer %s at %s", name, url)
            text = await self.fetch(url)
            if text:
                combined_text += "\n" + text
            await asyncio.sleep(self.delay_ms / 1000)

        if not combined_text.strip():
            logger.error("No content scraped for retailer %s", name)
            return None

        categories = _extract_categories(combined_text)
        sample_products = _extract_products(combined_text, max_items=20)
        has_tryon = detect_virtual_tryon(combined_text)
        tech_hints = extract_tech_hints(combined_text)
        tagline = _extract_tagline(combined_text)
        tryon_desc = _extract_tryon_sentence(combined_text)

        return CompetitorData(
            name=name,
            display_name=competitor.get("display_name", name),
            url=base_url,
            region=competitor["region"],
            type="retailer",
            scraped_at=datetime.utcnow(),
            tagline=tagline,
            has_virtual_tryon=has_tryon,
            tryon_description=tryon_desc,
            tech_hints=tech_hints,
            categories=categories,
            sample_products=sample_products,
        )


def _extract_categories(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw.title() for kw in CATEGORY_KEYWORDS if kw in text_lower]


def _extract_products(text: str, max_items: int = 20) -> list[SampleProduct]:
    products = []
    price_pattern = re.compile(r"(₹|AED|د\.إ|\$|£|€)\s*([\d,]+(?:\.\d+)?)")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = price_pattern.search(line)
        if match:
            symbol = match.group(1)
            price_str = match.group(2).replace(",", "")
            currency = CURRENCY_SYMBOLS.get(symbol, symbol)
            name = _find_nearby_product_name(lines, i)
            if name:
                products.append(
                    SampleProduct(
                        name=name,
                        price=float(price_str),
                        currency=currency,
                    )
                )
        if len(products) >= max_items:
            break
    return products


def _find_nearby_product_name(lines: list[str], price_line_idx: int) -> str | None:
    for offset in range(-3, 4):
        idx = price_line_idx + offset
        if 0 <= idx < len(lines) and idx != price_line_idx:
            candidate = lines[idx].strip()
            if 5 < len(candidate) < 100 and not re.search(r"₹|\$|AED|http", candidate):
                return candidate
    return None


def _extract_tagline(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if 10 < len(stripped) < 120:
            return stripped
    return None


def _extract_tryon_sentence(text: str) -> str | None:
    tryon_kw = ["virtual try-on", "try on", "augmented reality", "virtual fitting"]
    for line in text.splitlines():
        if any(kw in line.lower() for kw in tryon_kw):
            return line.strip()[:300]
    return None
```

- [ ] **Step 2: Verify import**

```bash
python -c "from scrapers.retailer_scraper import RetailerScraper; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scrapers/retailer_scraper.py
git commit -m "feat: add retailer scraper with product and category extraction"
```

---

## Task 9: Scheduler

**Files:**
- Create: `scheduler/scheduler.py`

- [ ] **Step 1: Create scheduler/scheduler.py**

```python
import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


async def run_scrape_pipeline():
    from main import run_all
    await run_all()


def start_scheduler():
    schedule_expr = os.getenv("SCRAPE_SCHEDULE", "0 2 * * *")
    parts = schedule_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid SCRAPE_SCHEDULE cron expression: {schedule_expr!r}")

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_scrape_pipeline, trigger=trigger, id="competitor_scrape")
    scheduler.start()
    logger.info("Scheduler started. Cron: %s", schedule_expr)

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from scheduler.scheduler import start_scheduler; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scheduler/scheduler.py
git commit -m "feat: add APScheduler cron daemon with .env-driven schedule"
```

---

## Task 10: CLI (main.py)

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create main.py**

```python
import argparse
import asyncio
import logging
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_competitors(config_path: str = "config/competitors.yaml") -> list[dict]:
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("competitors", [])


async def scrape_competitor(competitor: dict):
    from scrapers.platform_scraper import PlatformScraper
    from scrapers.retailer_scraper import RetailerScraper

    scraper = PlatformScraper() if competitor["type"] == "platform" else RetailerScraper()
    try:
        result = await scraper.scrape(competitor)
        return result
    except Exception as e:
        logger.error("Failed to scrape %s: %s", competitor["name"], e)
        return None


async def run_all(target: str | None = None):
    from storage.db import Database
    from storage.exporter import Exporter

    db_path = os.getenv("DB_PATH", "./data/competitors.db")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    max_concurrency = int(os.getenv("MAX_CONCURRENCY", "5"))

    db = Database(db_path)
    await db.init()

    competitors = load_competitors()
    if target:
        competitors = [c for c in competitors if c["name"] == target]
        if not competitors:
            logger.error("Competitor %r not found in config", target)
            return

    semaphore = asyncio.Semaphore(max_concurrency)

    async def bounded_scrape(comp):
        async with semaphore:
            return await scrape_competitor(comp)

    results = await asyncio.gather(*[bounded_scrape(c) for c in competitors])

    saved = 0
    for result in results:
        if result:
            await db.upsert(result)
            saved += 1

    logger.info("Scraped %d/%d competitors", saved, len(competitors))

    exporter = Exporter(db, output_dir=output_dir)
    csv_path = await exporter.export_csv()
    json_path = await exporter.export_json()
    logger.info("Exported to %s and %s", csv_path, json_path)


async def export_only():
    from storage.db import Database
    from storage.exporter import Exporter

    db_path = os.getenv("DB_PATH", "./data/competitors.db")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    db = Database(db_path)
    await db.init()
    exporter = Exporter(db, output_dir=output_dir)
    csv_path = await exporter.export_csv()
    json_path = await exporter.export_json()
    logger.info("Exported to %s and %s", csv_path, json_path)


def main():
    parser = argparse.ArgumentParser(description="MirrorFit Competitor Scraper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-now", action="store_true", help="Scrape all competitors immediately")
    group.add_argument("--schedule", action="store_true", help="Start scheduler daemon")
    group.add_argument("--export", action="store_true", help="Export DB to CSV + JSON")
    parser.add_argument("--target", type=str, help="Scrape single competitor by name")

    args = parser.parse_args()

    if args.run_now:
        asyncio.run(run_all(target=args.target))
    elif args.schedule:
        from scheduler.scheduler import start_scheduler
        start_scheduler()
    elif args.export:
        asyncio.run(export_only())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI help works**

```bash
python main.py --help
```

Expected output:
```
usage: main.py [-h] (--run-now | --schedule | --export) [--target TARGET]
...
```

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add CLI with --run-now, --schedule, --export, --target"
```

---

## Task 11: pytest.ini + Final Test Run

**Files:**
- Create: `pytest.ini`

- [ ] **Step 1: Create pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass (test_models, test_storage, test_exporter, test_base_scraper)

- [ ] **Step 3: Create .gitignore**

```
.env
data/
output/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Final commit**

```bash
git add pytest.ini .gitignore
git commit -m "chore: add pytest config and gitignore"
```

---

## Task 12: Smoke Test Single Competitor

- [ ] **Step 1: Run against single competitor**

```bash
python main.py --run-now --target vue_ai
```

Expected: logs show scrape attempt, `output/` dir has dated CSV + JSON files.

- [ ] **Step 2: Verify output files exist**

```bash
ls output/
```

Expected: `competitors_<today>.csv` and `competitors_<today>.json`

- [ ] **Step 3: Inspect JSON**

```bash
python -c "import json; print(json.dumps(json.load(open('output/competitors_$(date +%Y-%m-%d).json')), indent=2))"
```

Expected: JSON with `global` → `platform` → `vue_ai` entry.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: smoke test verified, project complete"
```

---

## Self-Review Checklist

- [x] All spec sections covered: targets, schema, scraper design, storage, exporter, scheduler, CLI, `.env`
- [x] No TBD/TODO placeholders — every step has actual code
- [x] Types consistent: `CompetitorData`, `SampleProduct` defined in Task 3, used in Tasks 4-10
- [x] Method names consistent: `db.upsert()`, `db.fetch_all()`, `db.fetch_by_region()` — same across storage tasks
- [x] `run_all()` in main.py matches what scheduler calls in `scheduler.py`
- [x] `competitors.yaml` structure matches `load_competitors()` dict access patterns
- [x] `robots.txt` — crawl4ai respects it by default; no extra code needed
- [x] Error log: logger writes to stdout — redirect to file via shell if needed (`2>&1 | tee output/scrape.log`)
