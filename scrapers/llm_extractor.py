import json
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_MAX_CONTENT_CHARS = 12000

_PLATFORM_PROMPT = """\
You are a competitive intelligence analyst. Extract structured information from this AI/tech company's website content.

Return ONLY valid JSON with exactly these fields:
{
  "tagline": "main value proposition or tagline (string, max 120 chars)",
  "about": "what the company does, product/service description (string, max 300 chars)",
  "pricing_plans": ["list of pricing plan names and prices found, e.g. Starter - $99/month"],
  "has_virtual_tryon": true or false,
  "tryon_description": "description of virtual try-on/AR fitting feature, or null",
  "tech_hints": ["list of specific technologies: AR, AI, 3D, LiDAR, computer vision, etc."],
  "social_links": {"instagram": "url or null", "facebook": "url or null", "youtube": "url or null", "tiktok": "url or null", "linkedin": "url or null", "twitter": "url or null"},
  "has_newsletter": true or false,
  "ad_tech": ["list of marketing/ad tech detected: Meta Pixel, Google Analytics, GTM, Klaviyo, HubSpot, Intercom, etc."]
}"""

_RETAILER_PROMPT = """\
You are a competitive intelligence analyst. Extract structured information from this fashion/retail e-commerce website.

Return ONLY valid JSON with exactly these fields:
{
  "tagline": "brand tagline or value proposition (string, max 120 chars)",
  "about": "what this retailer sells and their market positioning (string, max 300 chars)",
  "has_virtual_tryon": true or false,
  "tryon_description": "description of virtual try-on/AR fitting feature, or null",
  "tech_hints": ["specific technologies: AR, AI, 3D body scan, etc."],
  "categories": ["product categories e.g. Men, Women, Kids, Accessories, Footwear"],
  "sample_products": [{"name": "product name", "price": 999.0, "currency": "INR"}],
  "social_links": {"instagram": "url or null", "facebook": "url or null", "youtube": "url or null", "tiktok": "url or null", "linkedin": "url or null", "twitter": "url or null"},
  "has_newsletter": true or false,
  "ad_tech": ["list of marketing/ad tech detected: Meta Pixel, Google Analytics, GTM, Klaviyo, Mailchimp, etc."]
}
For sample_products: extract up to 10 actual products with real prices. Use 3-letter currency codes (INR, AED, USD). Omit if no products visible."""

_INFLUENCER_PROMPT = """\
You are an influencer marketing analyst. Extract a list of fashion influencers from this page.

Return ONLY valid JSON with exactly this structure:
{
  "influencers": [
    {
      "handle": "instagram_handle_without_at_symbol",
      "name": "Full Name",
      "followers": 150000,
      "niche": ["women fashion", "ethnic wear", "streetwear"],
      "region": "india",
      "bio": "short bio or description (max 200 chars)",
      "engagement_rate": "3.5%",
      "profile_url": "https://instagram.com/handle"
    }
  ]
}
Rules:
- handle: lowercase, no @ symbol, use instagram handle if available else YouTube/TikTok
- followers: integer (convert 1.2M → 1200000, 500K → 500000)
- region: must be exactly "india", "uae", or "global"
- niche: list of fashion sub-niches they cover
- Extract up to 40 influencers from this page
- Only include fashion/lifestyle/beauty influencers, skip non-fashion"""

_EVENT_PROMPT = """\
You are a fashion industry analyst. Extract ONLY fashion, apparel, textile, beauty, lifestyle, or retail industry events from this page.

INCLUDE: fashion weeks, garment/textile trade shows, apparel exhibitions, beauty expos, retail conferences, clothing trade fairs, designer shows, style summits, fabric fairs, fashion awards.
EXCLUDE: pharmaceutical, medical, food, automotive, construction, IT/software, agriculture, chemical, or other non-fashion events. If unsure, skip it.

Return ONLY valid JSON with exactly this structure:
{
  "events": [
    {
      "name": "Event Full Name",
      "event_type": "fashion week / trade show / exhibition / conference / awards",
      "location": "City, Country",
      "region": "india",
      "start_date": "YYYY-MM-DD or YYYY-MM (use best available format)",
      "end_date": "YYYY-MM-DD or YYYY-MM or null",
      "organizer": "Organizer name",
      "description": "Brief description of the event (max 200 chars)",
      "target_audience": ["designers", "retailers", "brands", "buyers", "consumers"],
      "website": "https://event-website.com or null"
    }
  ]
}
Rules:
- region: must be exactly "india", "uae", or "global"
- event_type: one of fashion week / trade show / exhibition / conference / awards / summit
- Extract all fashion/apparel/textile/beauty/retail events found on the page, up to 30
- Include both upcoming and past annual recurring events (scraped dates will be filtered later)
- Prefer exact dates (YYYY-MM-DD) over month-only when available"""


async def extract_with_llm(text: str, competitor_type: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — skipping LLM extraction")
        return None

    prompt = _PLATFORM_PROMPT if competitor_type == "platform" else _RETAILER_PROMPT
    content = text[:_MAX_CONTENT_CHARS]

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Website content (markdown):\n\n{content}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except Exception as e:
        logger.error("LLM extraction failed: %s", e)
        return None


async def extract_influencers_with_llm(text: str) -> list[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — skipping LLM extraction")
        return []

    content = text[:_MAX_CONTENT_CHARS]
    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _INFLUENCER_PROMPT},
                {"role": "user", "content": f"Page content (markdown):\n\n{content}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = json.loads(response.choices[0].message.content)
        return raw.get("influencers") or []
    except Exception as e:
        logger.error("Influencer LLM extraction failed: %s", e)
        return []


async def extract_events_with_llm(text: str) -> list[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — skipping LLM extraction")
        return []

    content = text[:_MAX_CONTENT_CHARS]
    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _EVENT_PROMPT},
                {"role": "user", "content": f"Page content (markdown):\n\n{content}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = json.loads(response.choices[0].message.content)
        return raw.get("events") or []
    except Exception as e:
        logger.error("Event LLM extraction failed: %s", e)
        return []
