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
