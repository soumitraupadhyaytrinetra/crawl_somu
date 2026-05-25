import asyncio
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

_JINA_SEARCH = "https://s.jina.ai/"

_SKIP_DOMAINS = {
    "linkedin.com", "instagram.com", "facebook.com", "twitter.com",
    "youtube.com", "tiktok.com", "wikipedia.org", "reddit.com",
    "amazon.com", "flipkart.com", "google.com", "bing.com",
    "pinterest.com", "snapchat.com", "whatsapp.com", "telegram.org",
}

_COMPETITOR_QUERIES = [
    # AR / virtual try-on platforms
    "virtual try-on fashion platform AI software",
    "AR fitting room e-commerce platform startup",
    "fashion AI body measurement sizing platform",
    "virtual fitting room fashion brand technology",
    # Indian retailers
    "Indian fashion ecommerce women ethnic wear online retailer",
    "India women clothing brand online ethnic western wear",
    "India fashion brand saree kurta online store",
    # UAE retailers
    "Dubai UAE online fashion retailer women clothing",
    "UAE modest fashion hijab abaya online store",
    # Global fashion retailers with tech
    "fashion retailer augmented reality virtual try-on feature",
    "online fashion brand virtual styling AI recommendation",
]

_EVENT_QUERIES = [
    "upcoming fashion trade shows India 2026",
    "fashion exhibition apparel India 2026",
    "textile garment trade fair India 2026",
    "fashion events Dubai UAE 2026",
    "fashion week India schedule 2026",
    "apparel retail trade show global 2026",
    "fashion conference summit 2026",
    "beauty cosmetics expo India UAE 2026",
]


async def _jina_search(query: str, api_key: str | None = None) -> str:
    encoded = query.replace(" ", "+")
    url = f"{_JINA_SEARCH}{encoded}"
    headers = {"Accept": "text/markdown"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text
            logger.warning("Jina search '%s' → %d", query, resp.status_code)
        except Exception as e:
            logger.warning("Jina search failed '%s': %s", query, e)
    return ""


def _extract_urls(md: str) -> list[str]:
    raw = re.findall(r'https?://[^\s\)\]\"\'<>]+', md)
    seen_domains: set[str] = set()
    result = []
    for u in raw:
        u = u.rstrip(".,;:/")
        domain = re.sub(r'^https?://(www\.)?', '', u).split('/')[0].lower()
        if not domain or domain in _SKIP_DOMAINS or domain in seen_domains:
            continue
        seen_domains.add(domain)
        result.append(u)
    return result


def _domain(url: str) -> str:
    return re.sub(r'^https?://(www\.)?', '', url).split('/')[0].lower()


async def discover_competitors(existing_domains: set[str] | None = None) -> list[dict]:
    api_key = os.getenv("JINA_API_KEY")
    existing = existing_domains or set()
    found: dict[str, dict] = {}

    for query in _COMPETITOR_QUERIES:
        md = await _jina_search(query, api_key)
        if not md:
            await asyncio.sleep(3)
            continue
        urls = _extract_urls(md)
        for url in urls[:6]:
            d = _domain(url)
            if d in existing or d in found:
                continue
            region = "global"
            if any(k in query.lower() for k in ["india", "indian", "saree", "kurta"]):
                region = "india"
            elif any(k in query.lower() for k in ["uae", "dubai", "hijab", "abaya"]):
                region = "uae"
            comp_type = "platform" if any(
                k in query.lower() for k in ["platform", "ar ", "fitting room", "body measurement", "ai software", "technology", "startup"]
            ) else "retailer"
            found[d] = {
                "name": d.replace(".", "_").replace("-", "_"),
                "display_name": d,
                "url": f"https://www.{d}" if not url.startswith("https://www") else url.split("/")[0] + "//" + url.split("/")[2],
                "region": region,
                "type": comp_type,
                "scrape_paths": ["/"],
            }
        await asyncio.sleep(3)

    logger.info("Discovery found %d new competitor domains", len(found))
    return list(found.values())


async def discover_event_sources() -> list[dict]:
    api_key = os.getenv("JINA_API_KEY")
    sources: list[dict] = []
    seen: set[str] = set()

    for query in _EVENT_QUERIES:
        md = await _jina_search(query, api_key)
        if not md:
            await asyncio.sleep(3)
            continue
        urls = _extract_urls(md)
        region = "global"
        if any(k in query.lower() for k in ["india", "indian"]):
            region = "india"
        elif any(k in query.lower() for k in ["dubai", "uae"]):
            region = "uae"
        for url in urls[:5]:
            key = f"{_domain(url)}_{region}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "name": f"disc_{_domain(url)}_{region}",
                    "url": url,
                    "region": region,
                    "scrape_paths": ["/"],
                })
        await asyncio.sleep(3)

    logger.info("Discovery found %d event sources", len(sources))
    return sources
