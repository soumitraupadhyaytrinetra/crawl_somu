import argparse
import asyncio
import io
import logging
import os
import sys
import yaml
from dotenv import load_dotenv

load_dotenv()

# UTF-8 fix for Windows (must be before logging.basicConfig)
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent


def load_yaml_list(filename: str, key: str) -> list[dict]:
    path = _PROJECT_ROOT / "config" / filename
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get(key, [])


def load_competitors() -> list[dict]:
    return load_yaml_list("competitors.yaml", "competitors")


def load_influencer_sources() -> list[dict]:
    return load_yaml_list("influencer_sources.yaml", "influencer_sources")


def load_event_sources() -> list[dict]:
    return load_yaml_list("events.yaml", "events")


def load_influencer_seeds() -> list[dict]:
    return load_yaml_list("influencer_seeds.yaml", "influencer_seeds")


async def scrape_competitor(competitor: dict):
    from scrapers.platform_scraper import PlatformScraper
    from scrapers.retailer_scraper import RetailerScraper

    scraper = PlatformScraper() if competitor["type"] == "platform" else RetailerScraper()
    try:
        return await scraper.scrape(competitor)
    except Exception as e:
        logger.error("Failed to scrape competitor %s: %s", competitor["name"], e)
        return None


async def scrape_influencer_source(source: dict):
    from scrapers.influencer_scraper import InfluencerScraper

    scraper = InfluencerScraper()
    try:
        return await scraper.scrape(source)
    except Exception as e:
        logger.error("Failed to scrape influencer source %s: %s", source["name"], e)
        return []


async def scrape_event_source(source: dict):
    from scrapers.event_scraper import EventScraper

    scraper = EventScraper()
    try:
        return await scraper.scrape(source)
    except Exception as e:
        logger.error("Failed to scrape event source %s: %s", source["name"], e)
        return []


def _build_topic_event_sources(topic: str) -> list[dict]:
    encoded = topic.lower().replace(" ", "+")
    q = topic.lower().replace(" ", "%20")
    return [
        {"name": f"10times_topic_{encoded}", "url": f"https://10times.com/events?q={encoded}", "region": "global", "scrape_paths": ["/"]},
        {"name": f"10times_topic_{encoded}_india", "url": f"https://10times.com/events?q={encoded}&cl=India", "region": "india", "scrape_paths": ["/"]},
        {"name": f"10times_topic_{encoded}_uae", "url": f"https://10times.com/events?q={encoded}&cl=UAE", "region": "uae", "scrape_paths": ["/"]},
        {"name": f"eventbrite_topic_{encoded}", "url": f"https://www.eventbrite.com/d/online/{encoded}--events/", "region": "global", "scrape_paths": ["/"]},
        {"name": f"eventbrite_topic_{encoded}_india", "url": f"https://www.eventbrite.com/d/india/{encoded}--events/", "region": "india", "scrape_paths": ["/"]},
        {"name": f"eventseye_topic_{encoded}", "url": f"https://www.eventseye.com/fairs/search.html?kw={q}", "region": "global", "scrape_paths": ["/"]},
        {"name": f"biztrade_topic_{encoded}", "url": f"https://www.biztradeshows.com/trade-events/?keyword={q}", "region": "global", "scrape_paths": ["/"]},
    ]


async def run_all(target: str | None = None, skip_competitors: bool = False,
                  skip_influencers: bool = False, skip_events: bool = False,
                  max_sources: int | None = None, topic_events: str | None = None):
    from storage.db import Database
    from storage.exporter import Exporter

    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/mirrorfit")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    max_concurrency = int(os.getenv("MAX_CONCURRENCY", "5"))

    db = Database(db_url)
    await db.init()

    semaphore = asyncio.Semaphore(max_concurrency)

    # ── Competitors ────────────────────────────────────────────────────────
    if not skip_competitors:
        competitors = load_competitors()
        if target:
            competitors = [c for c in competitors if c["name"] == target]
            if not competitors:
                logger.error("Competitor %r not found in config", target)
        else:
            from scrapers.discovery import discover_competitors, _domain
            existing_domains = {_domain(c["url"]) for c in competitors if c.get("url")}
            discovered = await discover_competitors(existing_domains)
            logger.info("Adding %d discovered competitors to %d from config", len(discovered), len(competitors))
            competitors = competitors + discovered
        if max_sources:
            competitors = competitors[:max_sources]

        async def bounded_competitor(comp):
            async with semaphore:
                return await scrape_competitor(comp)

        results = await asyncio.gather(*[bounded_competitor(c) for c in competitors])
        saved = 0
        for r in results:
            if r and await _save_competitor(db, r):
                saved += 1
        logger.info("Scraped %d/%d competitors", saved, len(competitors))

    # ── Influencers ────────────────────────────────────────────────────────
    if not skip_influencers:
        inf_saved = 0
        apify_key = os.getenv("APIFY_API_KEY")

        if apify_key:
            # Apify path: discover influencers via Instagram user search
            from scrapers.apify_scraper import ApifyScraper
            apify = ApifyScraper()

            # Clear old mixed data so only Apify results remain
            await db.clear_influencers()

            region_results = await asyncio.gather(
                apify.discover_influencers("india"),
                apify.discover_influencers("uae"),
                apify.discover_influencers("global"),
            )
            all_inf: list = [inf for r in region_results for inf in r]

            for inf in all_inf:
                try:
                    await db.upsert_influencer(inf)
                    inf_saved += 1
                except Exception as e:
                    logger.error("Failed to save influencer %s: %s", inf.handle, e)
            logger.info("Apify: saved %d influencers total", inf_saved)

        else:
            # Fallback: seed list + directory scraping (no Apify)
            from scrapers.instagram_scraper import InstagramScraper
            seeds = load_influencer_seeds()
            if seeds:
                ig_scraper = InstagramScraper()
                async def bounded_seed(seed):
                    async with semaphore:
                        return await ig_scraper.enrich_from_profile(seed)
                seed_results = await asyncio.gather(*[bounded_seed(s) for s in seeds])
                for inf in seed_results:
                    try:
                        await db.upsert_influencer(inf)
                        inf_saved += 1
                    except Exception as e:
                        logger.error("Failed to save influencer %s: %s", inf.handle, e)

            inf_sources = load_influencer_sources()
            if inf_sources:
                async def bounded_influencer(src):
                    async with semaphore:
                        return await scrape_influencer_source(src)
                inf_results = await asyncio.gather(*[bounded_influencer(s) for s in inf_sources])
                for influencer_list in inf_results:
                    for inf in (influencer_list or []):
                        try:
                            await db.upsert_influencer(inf)
                            inf_saved += 1
                        except Exception as e:
                            logger.error("Failed to save influencer %s: %s", inf.handle, e)

        logger.info("Total influencers saved: %d", inf_saved)

    # ── Events ─────────────────────────────────────────────────────────────
    if not skip_events:
        if topic_events:
            event_sources = _build_topic_event_sources(topic_events)
            logger.info("Topic scrape '%s': %d sources", topic_events, len(event_sources))
        else:
            event_sources = load_event_sources()
            from scrapers.discovery import discover_event_sources, _domain
            existing_evt_domains = {_domain(e["url"]) for e in event_sources if e.get("url")}
            discovered_evt = await discover_event_sources()
            new_evt = [e for e in discovered_evt if _domain(e["url"]) not in existing_evt_domains]
            logger.info("Adding %d discovered event sources to %d from config", len(new_evt), len(event_sources))
            event_sources = event_sources + new_evt
            if max_sources:
                event_sources = event_sources[:max_sources]
        if event_sources:
            async def bounded_event(src):
                async with semaphore:
                    return await scrape_event_source(src)

            evt_results = await asyncio.gather(*[bounded_event(s) for s in event_sources])
            evt_saved = 0
            for event_list in evt_results:
                for evt in (event_list or []):
                    try:
                        await db.upsert_event(evt)
                        evt_saved += 1
                    except Exception as e:
                        logger.error("Failed to save event %s: %s", evt.name, e)
            logger.info("Saved %d events from %d sources", evt_saved, len(event_sources))

    # ── Export ─────────────────────────────────────────────────────────────
    exporter = Exporter(db, output_dir=output_dir)
    csv_path = await exporter.export_csv()
    apify_only = bool(os.getenv("APIFY_API_KEY"))
    inf_csv = await exporter.export_influencers_csv(apify_only=apify_only)
    evt_csv = await exporter.export_events_csv()
    json_path = await exporter.export_json()
    logger.info("Exported:")
    logger.info("  Competitors  → %s", csv_path)
    logger.info("  Influencers  → %s", inf_csv)
    logger.info("  Events       → %s", evt_csv)
    logger.info("  Full report  → %s", json_path)


async def _save_competitor(db, result) -> bool:
    try:
        await db.upsert(result)
        return True
    except Exception as e:
        logger.error("Failed to save competitor %s: %s", result.name, e)
        return False


async def export_only():
    from storage.db import Database
    from storage.exporter import Exporter

    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/mirrorfit")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    db = Database(db_url)
    await db.init()
    exporter = Exporter(db, output_dir=output_dir)
    apify_only = bool(os.getenv("APIFY_API_KEY"))
    csv_path = await exporter.export_csv()
    inf_csv = await exporter.export_influencers_csv(apify_only=apify_only)
    evt_csv = await exporter.export_events_csv()
    json_path = await exporter.export_json()
    logger.info("Exported:")
    logger.info("  Competitors  → %s", csv_path)
    logger.info("  Influencers  → %s", inf_csv)
    logger.info("  Events       → %s", evt_csv)
    logger.info("  Full report  → %s", json_path)


def main():
    parser = argparse.ArgumentParser(description="MirrorFit Intelligence Scraper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-now", action="store_true", help="Scrape all data immediately")
    group.add_argument("--schedule", action="store_true", help="Start scheduler daemon")
    group.add_argument("--export", action="store_true", help="Export DB to CSV + JSON")
    parser.add_argument("--target", type=str, help="Scrape single competitor by name")
    parser.add_argument("--only-competitors", action="store_true", help="Skip influencers and events")
    parser.add_argument("--only-influencers", action="store_true", help="Skip competitors and events")
    parser.add_argument("--only-events", action="store_true", help="Skip competitors and influencers")
    parser.add_argument("--max-sources", type=int, default=None, help="Limit number of sources per section")
    parser.add_argument("--topic-events", type=str, default=None, help="Scrape events for a specific topic/category")

    args = parser.parse_args()

    skip_competitors = args.only_influencers or args.only_events
    skip_influencers = args.only_competitors or args.only_events
    skip_events = args.only_competitors or args.only_influencers

    if args.run_now:
        asyncio.run(run_all(
            target=args.target,
            skip_competitors=skip_competitors,
            skip_influencers=skip_influencers,
            skip_events=skip_events,
            max_sources=args.max_sources,
            topic_events=args.topic_events,
        ))
    elif args.schedule:
        from scheduler.scheduler import start_scheduler
        start_scheduler()
    elif args.export:
        asyncio.run(export_only())


if __name__ == "__main__":
    main()
