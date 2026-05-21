# MirrorFit AI Competitor Scraper — Design Spec
Date: 2026-05-18

## Overview

Modular web scraping framework using crawl4ai to collect competitive intelligence on:
- AI virtual try-on platforms (global)
- Fashion retailers with try-on features (India + UAE/Dubai)

Output: SQLite database + CSV + JSON. Manual trigger or cron schedule via `.env`.

---

## Architecture

```
crawlscraping/
├── .env                        # runtime config (schedule, paths, concurrency)
├── config/
│   └── competitors.yaml        # all targets, URLs, scrape rules
├── scrapers/
│   ├── base_scraper.py         # crawl4ai wrapper, retry logic, shared extraction
│   ├── platform_scraper.py     # AI try-on platforms
│   └── retailer_scraper.py     # fashion e-commerce retailers
├── storage/
│   ├── db.py                   # SQLite schema + CRUD
│   └── exporter.py             # CSV + JSON export
├── scheduler/
│   └── scheduler.py            # APScheduler reads SCRAPE_SCHEDULE from .env
├── main.py                     # CLI: --run-now | --schedule | --export
├── requirements.txt
└── output/                     # exported CSV + JSON files
```

---

## Environment Config (.env)

```env
SCRAPE_SCHEDULE=0 2 * * *     # cron expression — default: 2am daily
OUTPUT_DIR=./output
DB_PATH=./data/competitors.db
MAX_CONCURRENCY=5
LOG_LEVEL=INFO
USER_AGENT=Mozilla/5.0 (compatible; MirrorFitBot/1.0)
REQUEST_DELAY_MS=1500          # polite delay between requests
```

---

## Competitor Targets

### AI Try-On Platforms (Global)
| Name | URL |
|------|-----|
| Vue.ai | https://vue.ai |
| Zeekit (Walmart) | https://www.walmart.com/cp/virtual-try-on |
| Snap AR Try-On | https://ar.snap.com/shopping |
| Zakeke | https://www.zakeke.com |
| Fit:Match | https://www.fitmatch.ai |
| Sizer.me | https://sizer.me |
| 3DLOOK | https://3dlook.ai |

### Fashion Retailers — India
| Name | URL |
|------|-----|
| Myntra | https://www.myntra.com |
| Nykaa Fashion | https://www.nykaafashion.com |
| Ajio | https://www.ajio.com |
| Flipkart Fashion | https://www.flipkart.com/clothing-and-accessories |
| Meesho | https://meesho.com |
| Tata Cliq | https://www.tatacliq.com |

### Fashion Retailers — UAE/Dubai
| Name | URL |
|------|-----|
| Noon Fashion | https://www.noon.com/uae-en/fashion |
| Namshi | https://en-ae.namshi.com |
| Ounass | https://www.ounass.ae |
| Level Shoes | https://www.levelshoes.com |
| 6thStreet | https://en-ae.6thstreet.com |
| Max Fashion | https://www.maxfashion.com/ae |

---

## Data Schema

```python
Competitor {
    id: int (PK, auto)
    name: str
    url: str
    region: enum[india, uae, global]
    type: enum[platform, retailer]
    scraped_at: datetime

    # Business Info
    tagline: str
    about: str
    pricing_plans: JSON list[str]

    # Try-On Feature Intelligence
    has_virtual_tryon: bool
    tryon_description: str
    tech_hints: JSON list[str]   # keywords: AR, AI, 3D, LiDAR, etc.

    # Products
    categories: JSON list[str]
    sample_products: JSON list[{name, price, currency, image_url}]  # max 20 per run
}
```

---

## Scraper Design

### base_scraper.py
- Wraps crawl4ai `AsyncWebCrawler`
- Handles: JS rendering, retries (3x with backoff), `REQUEST_DELAY_MS` between requests
- Extracts raw markdown + structured JSON via crawl4ai's LLM extraction strategy
- Returns normalized dict matching schema above

### platform_scraper.py
- Targets: pricing pages, features pages, about pages
- Extra focus: tech stack hints (scrapes meta tags, footer text, job listings hints)
- Uses crawl4ai `JsonCssExtractionStrategy` where CSS selectors work; falls back to LLM extraction

### retailer_scraper.py
- Targets: homepage, top category pages, try-on/AR feature pages
- Extracts: product categories, sample products (name + price + image), any virtual try-on mentions
- Respects `robots.txt` — skips disallowed paths

---

## Storage

### SQLite (db.py)
- Single `competitors` table matching schema above
- Upsert on `(name, scraped_at::date)` — one record per competitor per day
- Index on `region`, `type`, `scraped_at`

### Exporter (exporter.py)
- On demand or post-scrape: exports full DB to `output/competitors_YYYY-MM-DD.csv` and `output/competitors_YYYY-MM-DD.json`
- JSON export groups by region + type for easy comparison

---

## Scheduler

```python
# scheduler.py
# Reads SCRAPE_SCHEDULE from .env
# Uses APScheduler CronTrigger
# Runs full scrape pipeline then auto-exports
```

---

## CLI (main.py)

```bash
python main.py --run-now          # scrape all competitors immediately
python main.py --schedule         # start scheduler daemon (uses .env cron)
python main.py --export           # export latest DB snapshot to CSV + JSON
python main.py --target myntra    # scrape single competitor by name
```

---

## Error Handling

- Per-competitor try/except — one failure never blocks others
- Failed targets logged with reason, retried once after full pass completes
- Rate limit detected (HTTP 429) → exponential backoff up to 3 attempts
- Partial data saved — better incomplete record than no record
- All errors written to `output/scrape_errors_YYYY-MM-DD.log`

---

## Testing

- `tests/test_base_scraper.py` — unit test extraction logic with mocked HTML fixtures
- `tests/test_storage.py` — SQLite write/read/upsert correctness
- `tests/test_exporter.py` — CSV + JSON output format validation
- No live network calls in tests — all fixtures are static HTML files

---

## Dependencies

```
crawl4ai>=0.4.0
apscheduler>=3.10.0
pydantic>=2.0
python-dotenv>=1.0
pyyaml>=6.0
aiosqlite>=0.19.0
pandas>=2.0          # for CSV export
```

---

## Out of Scope

- Proxy rotation (add later if sites block)
- Dashboard/UI (raw files sufficient for now)
- Price history tracking (current spec: daily snapshot only)
