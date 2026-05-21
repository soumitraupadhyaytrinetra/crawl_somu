import asyncio
import logging
import re
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from scrapers.models import InfluencerData

logger = logging.getLogger(__name__)

_FOLLOWER_PATTERN = re.compile(
    r"([\d,\.]+)\s*([KkMm])?\s*[Ff]ollower",
)
_ENGAGEMENT_PATTERN = re.compile(r"([\d\.]+)\s*%\s*engagement", re.IGNORECASE)


def _parse_followers(text: str) -> int | None:
    m = _FOLLOWER_PATTERN.search(text)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    suffix = (m.group(2) or "").upper()
    try:
        val = float(raw)
        if suffix == "K":
            val *= 1_000
        elif suffix == "M":
            val *= 1_000_000
        return int(val)
    except ValueError:
        return None


class InstagramScraper(BaseScraper):
    async def enrich_from_profile(self, seed: dict) -> InfluencerData:
        handle = seed["handle"]
        url = f"https://www.instagram.com/{handle}/"
        region = seed.get("region", "global")

        followers = seed.get("followers")
        bio = seed.get("bio")
        engagement_rate = seed.get("engagement_rate")

        # best-effort: Instagram blocks heavily but sometimes returns public data
        text = await self.fetch(url)
        if text:
            parsed_followers = _parse_followers(text)
            if parsed_followers:
                followers = parsed_followers
            em = _ENGAGEMENT_PATTERN.search(text)
            if em:
                engagement_rate = em.group(0)
            # extract bio from og:description style lines
            for line in text.splitlines():
                stripped = line.strip()
                if 20 < len(stripped) < 200 and "follower" not in stripped.lower():
                    if not bio:
                        bio = stripped
                    break
            logger.info("Enriched Instagram profile for @%s", handle)
        else:
            logger.warning("Could not fetch Instagram profile for @%s — using seed data", handle)

        return InfluencerData(
            handle=handle,
            name=seed.get("name"),
            platform=seed.get("platform", "instagram"),
            followers=followers,
            niche=seed.get("niche") or [],
            region=region,
            bio=bio,
            engagement_rate=engagement_rate,
            profile_url=seed.get("profile_url") or url,
            scraped_at=datetime.utcnow(),
            source_url=url,
        )
