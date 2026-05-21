import asyncio
import logging
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from scrapers.llm_extractor import extract_events_with_llm
from scrapers.models import EventData

logger = logging.getLogger(__name__)

# Hard exclusion: words in event name that indicate non-fashion industries
_EXCLUDE_WORDS = {
    "pharma", "fharma", "process expo", "eco sustain", "chemical", "petroleum",
    "medical", "healthcare", "hospital", "food", "beverage", "agri",
    "automotive", "automobile", "construction", "infrastructure",
    "mining", "oil", "gas", "power", "energy", "telecom", "electronics",
    "cybersecurity", "blockchain", "fintech", "insurance", "banking",
    "education", "edtech", "hr tech", "logistics", "shipping",
}


def _is_fashion_relevant(name: str, description: str = "") -> bool:
    text = (name + " " + (description or "")).lower()
    return not any(w in text for w in _EXCLUDE_WORDS)


class EventScraper(BaseScraper):
    async def scrape(self, event_config: dict) -> list[EventData]:
        name = event_config["name"]
        base_url = event_config["url"]
        paths = event_config.get("scrape_paths", ["/"])
        region = event_config["region"]

        combined_text = ""
        for path in paths:
            url = base_url.rstrip("/") + path
            logger.info("Scraping event source %s at %s", name, url)
            text = await self.fetch(url)
            if text:
                combined_text += "\n" + text
            await asyncio.sleep(self.delay_ms / 1000)

        if not combined_text.strip():
            logger.error("No content scraped for event source %s", name)
            return []

        raw_list = await extract_events_with_llm(combined_text)
        if not raw_list:
            logger.warning("No events extracted from %s", name)
            return []

        events = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            event_name = item.get("name", "").strip()
            if not event_name:
                continue
            if not _is_fashion_relevant(event_name, item.get("description", "")):
                logger.debug("Skipping non-fashion event: %s", event_name)
                continue
            item_region = item.get("region", region)
            if item_region not in ("india", "uae", "global"):
                item_region = region
            events.append(
                EventData(
                    name=event_name,
                    event_type=item.get("event_type"),
                    location=item.get("location"),
                    region=item_region,
                    start_date=item.get("start_date"),
                    end_date=item.get("end_date"),
                    website=item.get("website") or base_url,
                    organizer=item.get("organizer"),
                    description=item.get("description"),
                    target_audience=item.get("target_audience") or [],
                    scraped_at=datetime.utcnow(),
                    source_url=base_url,
                )
            )

        logger.info("Extracted %d events from %s", len(events), name)
        return events
