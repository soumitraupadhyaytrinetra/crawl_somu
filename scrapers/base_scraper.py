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

# Order matters: named-tier pattern first so that price-only matches
# are skipped as substrings of already-found full-line plans.
PRICING_PATTERNS = [
    r"(?:starter|basic|pro|professional|enterprise|free)\s*[-–]\s*[^\n]{3,50}",
    r"\$[\d,]+(?:\.\d+)?(?:/(?:mo|month|yr|year))?",
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
            if not cleaned:
                continue
            # Skip exact duplicates and items already contained in a found plan
            if any(cleaned in existing for existing in plans):
                continue
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
                        # crawl4ai 0.8.x: result.markdown is a MarkdownGenerationResult
                        # object with a raw_markdown field; use raw_markdown for plain str.
                        md = result.markdown
                        if hasattr(md, "raw_markdown"):
                            return md.raw_markdown
                        return str(md) if md is not None else None
                    logger.warning(
                        "Fetch failed %s attempt %d: %s",
                        url,
                        attempt + 1,
                        result.error_message,
                    )
            except Exception as e:
                logger.warning(
                    "Exception fetching %s attempt %d: %s", url, attempt + 1, e
                )
            if attempt < self.max_retries - 1:
                backoff = (2 ** attempt) * (self.delay_ms / 1000)
                await asyncio.sleep(backoff)
        return None

    async def scrape(self, competitor: dict) -> CompetitorData | None:
        raise NotImplementedError
