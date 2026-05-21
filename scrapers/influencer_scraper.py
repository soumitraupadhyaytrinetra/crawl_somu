import asyncio
import logging
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from scrapers.llm_extractor import extract_influencers_with_llm
from scrapers.models import InfluencerData

logger = logging.getLogger(__name__)


class InfluencerScraper(BaseScraper):
    async def scrape(self, source: dict) -> list[InfluencerData]:
        name = source["name"]
        url = source["url"]
        region = source["region"]

        logger.info("Scraping influencer source %s at %s", name, url)
        text = await self.fetch(url)

        if not text or not text.strip():
            logger.error("No content scraped for influencer source %s", name)
            return []

        raw_list = await extract_influencers_with_llm(text)
        if not raw_list:
            logger.warning("No influencers extracted from %s", name)
            return []

        influencers = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            handle = item.get("handle", "").strip().lstrip("@")
            if not handle:
                continue
            # Override region with source region if LLM gave something weird
            item_region = item.get("region", region)
            if item_region not in ("india", "uae", "global"):
                item_region = region
            followers_raw = item.get("followers")
            try:
                followers = int(followers_raw) if followers_raw is not None else None
            except (ValueError, TypeError):
                followers = None
            influencers.append(
                InfluencerData(
                    handle=handle,
                    name=item.get("name"),
                    platform="instagram",
                    followers=followers,
                    niche=item.get("niche") or [],
                    region=item_region,
                    bio=item.get("bio"),
                    engagement_rate=item.get("engagement_rate"),
                    profile_url=item.get("profile_url") or f"https://instagram.com/{handle}",
                    scraped_at=datetime.utcnow(),
                    source_url=url,
                )
            )

        logger.info("Extracted %d influencers from %s", len(influencers), name)
        return influencers
