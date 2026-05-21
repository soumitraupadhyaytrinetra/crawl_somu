import asyncio
import logging
from datetime import datetime

from scrapers.base_scraper import (
    BaseScraper,
    detect_virtual_tryon,
    extract_pricing_plans,
    extract_tech_hints,
)
from scrapers.llm_extractor import extract_with_llm
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

        extracted = await extract_with_llm(combined_text, "platform")

        if extracted:
            logger.info("LLM extraction succeeded for %s", name)
            return CompetitorData(
                name=name,
                display_name=competitor.get("display_name", name),
                url=base_url,
                region=competitor["region"],
                type="platform",
                scraped_at=datetime.utcnow(),
                tagline=extracted.get("tagline"),
                about=extracted.get("about"),
                pricing_plans=extracted.get("pricing_plans") or [],
                has_virtual_tryon=bool(extracted.get("has_virtual_tryon", False)),
                tryon_description=extracted.get("tryon_description"),
                tech_hints=extracted.get("tech_hints") or [],
                categories=[],
                sample_products=[],
                social_links=extracted.get("social_links") or {},
                has_newsletter=bool(extracted.get("has_newsletter", False)),
                ad_tech=extracted.get("ad_tech") or [],
            )

        # Fallback: regex extraction
        logger.warning("LLM extraction failed for %s — using regex fallback", name)
        return CompetitorData(
            name=name,
            display_name=competitor.get("display_name", name),
            url=base_url,
            region=competitor["region"],
            type="platform",
            scraped_at=datetime.utcnow(),
            tagline=_extract_first_line(combined_text),
            about=_extract_paragraph(combined_text),
            pricing_plans=extract_pricing_plans(combined_text),
            has_virtual_tryon=detect_virtual_tryon(combined_text),
            tryon_description=_extract_tryon_sentence(combined_text),
            tech_hints=extract_tech_hints(combined_text),
            categories=[],
            sample_products=[],
        )


def _extract_first_line(text: str, max_len: int = 150) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if len(stripped) > 10 and not stripped.startswith("![]") and not stripped.startswith("["):
            return stripped[:max_len]
    return None


def _extract_paragraph(text: str, max_len: int = 500) -> str | None:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    return paragraphs[0][:max_len] if paragraphs else None


def _extract_tryon_sentence(text: str) -> str | None:
    tryon_kw = ["virtual try-on", "try on", "augmented reality", "virtual fitting"]
    for line in text.splitlines():
        if any(kw in line.lower() for kw in tryon_kw):
            return line.strip()[:300]
    return None
