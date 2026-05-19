import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


async def run_scrape_pipeline():
    from main import run_all
    await run_all()


def start_scheduler():
    schedule_expr = os.getenv("SCRAPE_SCHEDULE", "0 2 * * *")
    parts = schedule_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid SCRAPE_SCHEDULE cron expression: {schedule_expr!r}")

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )

    async def _run():
        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_scrape_pipeline, trigger=trigger, id="competitor_scrape")
        scheduler.start()
        logger.info("Scheduler started. Cron: %s", schedule_expr)
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            scheduler.shutdown()
            logger.info("Scheduler stopped.")

    asyncio.run(_run())
