import asyncio
import logging
import re
from datetime import datetime

from scrapers.base_scraper import (
    BaseScraper,
    detect_virtual_tryon,
    extract_tech_hints,
)
from scrapers.llm_extractor import extract_with_llm
from scrapers.models import CompetitorData, SampleProduct

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = [
    "men", "women", "kids", "accessories", "footwear", "ethnic",
    "western", "sportswear", "activewear", "bags", "jewellery",
    "beauty", "lingerie", "plus size",
]

CURRENCY_SYMBOLS = {
    "₹": "INR",
    "$": "USD",
    "AED": "AED",
    "د.إ": "AED",
    "£": "GBP",
    "€": "EUR",
}


class RetailerScraper(BaseScraper):
    async def scrape(self, competitor: dict) -> CompetitorData | None:
        name = competitor["name"]
        base_url = competitor["url"]
        paths = competitor.get("scrape_paths", ["/"])

        combined_text = ""
        for path in paths:
            url = base_url.rstrip("/") + path
            logger.info("Scraping retailer %s at %s", name, url)
            text = await self.fetch(url)
            if text:
                combined_text += "\n" + text
            await asyncio.sleep(self.delay_ms / 1000)

        if not combined_text.strip():
            logger.error("No content scraped for retailer %s", name)
            return None

        extracted = await extract_with_llm(combined_text, "retailer")

        if extracted:
            logger.info("LLM extraction succeeded for %s", name)
            raw_products = extracted.get("sample_products") or []
            sample_products = [
                SampleProduct(
                    name=p.get("name", ""),
                    price=float(p["price"]) if p.get("price") is not None else None,
                    currency=p.get("currency"),
                )
                for p in raw_products
                if isinstance(p, dict) and p.get("name")
            ]
            return CompetitorData(
                name=name,
                display_name=competitor.get("display_name", name),
                url=base_url,
                region=competitor["region"],
                type="retailer",
                scraped_at=datetime.utcnow(),
                tagline=extracted.get("tagline"),
                about=extracted.get("about"),
                has_virtual_tryon=bool(extracted.get("has_virtual_tryon", False)),
                tryon_description=extracted.get("tryon_description"),
                tech_hints=extracted.get("tech_hints") or [],
                categories=extracted.get("categories") or [],
                sample_products=sample_products,
            )

        # Fallback: regex extraction
        logger.warning("LLM extraction failed for %s — using regex fallback", name)
        return CompetitorData(
            name=name,
            display_name=competitor.get("display_name", name),
            url=base_url,
            region=competitor["region"],
            type="retailer",
            scraped_at=datetime.utcnow(),
            tagline=_extract_tagline(combined_text),
            has_virtual_tryon=detect_virtual_tryon(combined_text),
            tryon_description=_extract_tryon_sentence(combined_text),
            tech_hints=extract_tech_hints(combined_text),
            categories=_extract_categories(combined_text),
            sample_products=_extract_products(combined_text, max_items=20),
        )


def _extract_categories(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw.title() for kw in CATEGORY_KEYWORDS if kw in text_lower]


def _extract_products(text: str, max_items: int = 20) -> list[SampleProduct]:
    products = []
    price_pattern = re.compile(r"(₹|AED|د\.إ|\$|£|€)\s*([\d,]+(?:\.\d+)?)")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = price_pattern.search(line)
        if match:
            symbol = match.group(1)
            price_str = match.group(2).replace(",", "")
            currency = CURRENCY_SYMBOLS.get(symbol, symbol)
            name = _find_nearby_product_name(lines, i)
            if name:
                products.append(SampleProduct(name=name, price=float(price_str), currency=currency))
        if len(products) >= max_items:
            break
    return products


def _find_nearby_product_name(lines: list[str], price_line_idx: int) -> str | None:
    for offset in range(-3, 4):
        idx = price_line_idx + offset
        if 0 <= idx < len(lines) and idx != price_line_idx:
            candidate = lines[idx].strip()
            if 5 < len(candidate) < 100 and not re.search(r"₹|\$|AED|http", candidate):
                return candidate
    return None


def _extract_tagline(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if 10 < len(stripped) < 120 and not stripped.startswith("![]") and not stripped.startswith("["):
            return stripped
    return None


def _extract_tryon_sentence(text: str) -> str | None:
    tryon_kw = ["virtual try-on", "try on", "augmented reality", "virtual fitting"]
    for line in text.splitlines():
        if any(kw in line.lower() for kw in tryon_kw):
            return line.strip()[:300]
    return None
