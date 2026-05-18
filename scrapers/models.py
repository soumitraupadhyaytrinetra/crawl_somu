from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class SampleProduct(BaseModel):
    name: str
    price: float | None = None
    currency: str | None = None
    image_url: str | None = None


class CompetitorData(BaseModel):
    name: str
    display_name: str
    url: str
    region: Literal["india", "uae", "global"]
    type: Literal["platform", "retailer"]
    scraped_at: datetime | None = None

    tagline: str | None = None
    about: str | None = None
    pricing_plans: list[str] = []

    has_virtual_tryon: bool = False
    tryon_description: str | None = None
    tech_hints: list[str] = []

    categories: list[str] = []
    sample_products: list[SampleProduct] = []
