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

    # Marketing data
    social_links: dict = {}
    has_newsletter: bool = False
    ad_tech: list[str] = []


class InfluencerData(BaseModel):
    handle: str
    name: str | None = None
    platform: str = "instagram"
    followers: int | None = None
    niche: list[str] = []
    region: Literal["india", "uae", "global"] = "global"
    bio: str | None = None
    engagement_rate: str | None = None
    profile_url: str | None = None
    scraped_at: datetime | None = None
    source_url: str | None = None


class EventData(BaseModel):
    name: str
    event_type: str | None = None
    location: str | None = None
    region: Literal["india", "uae", "global"] = "global"
    start_date: str | None = None
    end_date: str | None = None
    website: str | None = None
    organizer: str | None = None
    description: str | None = None
    target_audience: list[str] = []
    scraped_at: datetime | None = None
    source_url: str | None = None
