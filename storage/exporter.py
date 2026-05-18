import csv
import json
import os
from datetime import date
from pathlib import Path

from storage.db import Database


class Exporter:
    def __init__(self, db: Database, output_dir: str = "./output"):
        self.db = db
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    async def export_csv(self) -> str:
        rows = await self.db.fetch_all()
        filename = f"competitors_{date.today().isoformat()}.csv"
        path = os.path.join(self.output_dir, filename)
        if not rows:
            return path
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return path

    async def export_json(self) -> str:
        rows = await self.db.fetch_all()
        filename = f"competitors_{date.today().isoformat()}.json"
        path = os.path.join(self.output_dir, filename)
        grouped: dict = {}
        for row in rows:
            region = row.get("region", "unknown")
            ctype = row.get("type", "unknown")
            grouped.setdefault(region, {}).setdefault(ctype, []).append(row)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, indent=2, ensure_ascii=False)
        return path
