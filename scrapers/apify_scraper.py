import asyncio
import logging
import os
from datetime import datetime

import httpx

from scrapers.models import InfluencerData

logger = logging.getLogger(__name__)

_RUN_SYNC_URL = (
    "https://api.apify.com/v2/acts/apify~instagram-scraper"
    "/run-sync-get-dataset-items"
)

# Search queries used to discover NEW influencers (beyond the seed list)
_DISCOVERY_QUERIES = {
    "india": [
        "indian fashion blogger",
        "ethnic wear india influencer",
        "indian style blogger",
        "bollywood fashion india",
        "kurti saree fashion blogger",
        "india ootd fashion",
        "desi fashion influencer",
        "indian outfit blogger",
        "delhi fashion blogger",
        "mumbai fashion influencer",
        "bangalore fashion blogger",
        "india western wear blogger",
        "indo western fashion",
        "saree blogger india",
    ],
    "uae": [
        "dubai fashion blogger",
        "modest fashion uae",
        "arab fashion influencer",
        "dubai style influencer",
        "uae fashion blogger",
        "abu dhabi fashion influencer",
        "hijab fashion blogger",
        "middle east fashion influencer",
        "gulf fashion blogger",
    ],
    "global": [
        "fashion influencer ootd",
        "style blogger fashion",
        "sustainable fashion influencer",
        "plus size fashion blogger",
        "luxury fashion influencer",
        "streetwear fashion blogger",
        "minimalist fashion blogger",
    ],
}

_FASHION_KEYWORDS = [
    "fashion", "style", "ootd", "outfit", "wear", "ethnic", "kurti",
    "saree", "hijab", "abaya", "modest", "luxury", "designer", "couture",
    "streetwear", "blogger", "influencer", "model",
]


def _infer_niche(bio: str) -> list[str]:
    bio_lower = bio.lower()
    niche = []
    if any(k in bio_lower for k in ["ethnic", "saree", "kurti", "kurta", "indian wear", "salwar"]):
        niche.append("ethnic wear")
    if any(k in bio_lower for k in ["modest", "hijab", "abaya", "covered"]):
        niche.append("modest fashion")
    if any(k in bio_lower for k in ["luxury", "designer", "couture", "haute"]):
        niche.append("luxury fashion")
    if any(k in bio_lower for k in ["street", "streetwear", "urban"]):
        niche.append("streetwear")
    if any(k in bio_lower for k in ["sustainable", "eco", "conscious"]):
        niche.append("sustainable fashion")
    if any(k in bio_lower for k in ["plus", "curvy", "body positive", "inclusive"]):
        niche.append("plus size fashion")
    if any(k in bio_lower for k in ["bridal", "wedding", "bride"]):
        niche.append("bridal")
    if not niche:
        niche = ["fashion"]
    return niche


def _parse_item(item: dict, region: str = "global") -> InfluencerData | None:
    handle = (item.get("username") or item.get("handle") or "").strip()
    if not handle:
        return None
    followers = item.get("followersCount") or item.get("followers")
    # Only keep accounts with meaningful reach
    if followers is not None and followers < 5_000:
        return None
    bio = (item.get("biography") or item.get("bio") or "").strip()
    # Skip non-fashion accounts
    if bio and not any(k in bio.lower() for k in _FASHION_KEYWORDS):
        return None
    return InfluencerData(
        handle=handle,
        name=item.get("fullName") or item.get("name"),
        platform="instagram",
        followers=followers,
        niche=_infer_niche(bio),
        region=region,
        bio=bio[:200] if bio else None,
        profile_url=f"https://www.instagram.com/{handle}/",
        scraped_at=datetime.utcnow(),
        source_url="apify:instagram-scraper",
    )


class ApifyScraper:
    def __init__(self):
        self.api_key = os.getenv("APIFY_API_KEY")
        if not self.api_key:
            raise ValueError("APIFY_API_KEY not set in .env")

    async def _call(self, payload: dict, timeout: int = 180) -> list[dict]:
        params = {"token": self.api_key}
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(_RUN_SYNC_URL, params=params, json=payload)
                if resp.status_code not in (200, 201):
                    logger.error("Apify error %d: %s", resp.status_code, resp.text[:300])
                    return []
                data = resp.json()
                return data if isinstance(data, list) else []
            except httpx.TimeoutException:
                logger.error("Apify request timed out (payload: %s)", list(payload.keys()))
                return []
            except Exception as e:
                logger.error("Apify request failed: %s", e)
                return []

    async def scrape_profiles(self, handles: list[str], region: str = "global") -> list[InfluencerData]:
        """Fetch live profile data for known handles via directUrls."""
        if not handles:
            return []
        urls = [f"https://www.instagram.com/{h}/" for h in handles]
        # Apify handles batches; split into 25 to avoid timeouts
        results = []
        for i in range(0, len(urls), 25):
            batch = urls[i:i + 25]
            payload = {
                "directUrls": batch,
                "resultsType": "details",
                "resultsLimit": len(batch),
            }
            logger.info("Apify scrape_profiles batch %d-%d (region=%s)", i, i + len(batch), region)
            items = await self._call(payload)
            for item in items:
                inf = _parse_item(item, region)
                if inf:
                    results.append(inf)
            if i + 25 < len(urls):
                await asyncio.sleep(3)
        logger.info("Apify scrape_profiles: got %d results for region=%s", len(results), region)
        return results

    async def discover_influencers(self, region: str) -> list[InfluencerData]:
        """Discover new influencers via Instagram user search."""
        queries = _DISCOVERY_QUERIES.get(region, _DISCOVERY_QUERIES["global"])
        results = []
        seen_handles = set()
        for query in queries:
            payload = {
                "searchType": "user",
                "search": query,
                "searchLimit": 50,
                "resultsType": "details",
                "resultsLimit": 50,
            }
            logger.info("Apify discover '%s' (region=%s)", query, region)
            items = await self._call(payload, timeout=120)
            for item in items:
                inf = _parse_item(item, region)
                if inf and inf.handle not in seen_handles:
                    seen_handles.add(inf.handle)
                    results.append(inf)
            await asyncio.sleep(2)
        logger.info("Apify discover: found %d influencers for region=%s", len(results), region)
        return results
