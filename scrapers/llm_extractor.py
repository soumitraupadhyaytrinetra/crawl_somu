import json
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Truncate combined markdown to keep costs low (~3k tokens of content)
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
  "tech_hints": ["list of specific technologies: AR, AI, 3D, LiDAR, computer vision, etc."]
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
  "sample_products": [{"name": "product name", "price": 999.0, "currency": "INR"}]
}
For sample_products: extract up to 10 actual products with real prices. Use 3-letter currency codes (INR, AED, USD). Omit if no products visible."""


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
