import asyncio
import logging
import os
import re as _re
from datetime import datetime

import html2text
import httpx
from dotenv import load_dotenv

from scrapers.models import CompetitorData, SampleProduct

load_dotenv()

_h2t = html2text.HTML2Text()
_h2t.ignore_links = False
_h2t.ignore_images = True
_h2t.body_width = 0

logger = logging.getLogger(__name__)

TECH_KEYWORDS = [
    "AR", "AI", "3D", "LiDAR", "augmented reality", "machine learning",
    "computer vision", "virtual try-on", "body scan", "deep learning",
    "neural network", "pose estimation",
]

TRYON_KEYWORDS = [
    "virtual try-on", "virtual tryon", "virtual try on",
    "augmented reality try", "augmented reality", "AR try-on",
    "virtual fitting room", "virtual fitting",
    "try before you buy",
    "see how it looks on you",
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
    for kw in TECH_KEYWORDS:
        if len(kw) <= 3:
            pattern = r'\b' + _re.escape(kw) + r'\b'
            if _re.search(pattern, text, _re.IGNORECASE) and kw not in found:
                found.append(kw)
        else:
            if kw.lower() in text.lower() and kw not in found:
                found.append(kw)
    return found


def extract_pricing_plans(text: str) -> list[str]:
    if not text:
        return []
    plans = []
    for pattern in PRICING_PATTERNS:
        matches = _re.findall(pattern, text, _re.IGNORECASE)
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
        headers = {"User-Agent": self.user_agent}
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        ct = resp.headers.get("content-type", "")
                        if "html" in ct:
                            return _h2t.handle(resp.text)
                        return resp.text
                    logger.warning("Fetch %s attempt %d status %d", url, attempt + 1, resp.status_code)
            except Exception as e:
                logger.warning("Exception fetching %s attempt %d: %s", url, attempt + 1, e)
            if attempt < self.max_retries - 1:
                await asyncio.sleep((2 ** attempt) * (self.delay_ms / 1000))
        return None

    async def scrape(self, competitor: dict) -> CompetitorData | None:
        raise NotImplementedError
