import csv
import json
import os
from datetime import datetime
from pathlib import Path

from storage.db import Database


class Exporter:
    def __init__(self, db: Database, output_dir: str = "./output"):
        self.db = db
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _ts(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d_%H%M")

    async def export_csv(self) -> str:
        rows = await self.db.fetch_all()
        filename = f"competitors_{self._ts()}.csv"
        path = os.path.join(self.output_dir, filename)
        fieldnames = [
            "id", "name", "display_name", "url", "region", "type",
            "scraped_at", "scraped_date", "tagline", "about", "pricing_plans",
            "has_virtual_tryon", "tryon_description", "tech_hints",
            "categories", "sample_products",
            "social_links", "has_newsletter", "ad_tech",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            if rows:
                writer.writerows(rows)
        return path

    async def export_influencers_csv(self, apify_only: bool = False) -> str:
        rows = (
            await self.db.fetch_apify_influencers()
            if apify_only
            else await self.db.fetch_all_influencers()
        )
        prefix = "influencers_apify" if apify_only else "influencers"
        filename = f"{prefix}_{self._ts()}.csv"
        path = os.path.join(self.output_dir, filename)
        fieldnames = [
            "id", "handle", "name", "platform", "followers", "niche",
            "region", "bio", "engagement_rate", "profile_url",
            "scraped_at", "scraped_date", "source_url",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            if rows:
                writer.writerows(rows)
        return path

    async def export_events_csv(self) -> str:
        rows = await self.db.fetch_all_events()
        filename = f"events_{self._ts()}.csv"
        path = os.path.join(self.output_dir, filename)
        fieldnames = [
            "id", "name", "event_type", "location", "region",
            "start_date", "end_date", "website", "organizer",
            "description", "target_audience", "scraped_at", "scraped_date", "source_url",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            if rows:
                writer.writerows(rows)
        return path

    async def export_json(self) -> str:
        competitors = await self.db.fetch_all()
        influencers = await self.db.fetch_all_influencers()
        events = await self.db.fetch_all_events()

        filename = f"full_report_{self._ts()}.json"
        path = os.path.join(self.output_dir, filename)

        grouped_competitors: dict = {}
        for row in competitors:
            region = row.get("region", "unknown")
            ctype = row.get("type", "unknown")
            grouped_competitors.setdefault(region, {}).setdefault(ctype, []).append(row)

        grouped_influencers: dict = {}
        for row in influencers:
            region = row.get("region", "unknown")
            grouped_influencers.setdefault(region, []).append(row)

        grouped_events: dict = {}
        for row in events:
            region = row.get("region", "unknown")
            grouped_events.setdefault(region, []).append(row)

        report = {
            "competitors": grouped_competitors,
            "influencers": grouped_influencers,
            "events": grouped_events,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return path
