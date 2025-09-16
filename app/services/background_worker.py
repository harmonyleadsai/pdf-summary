# app/services/background_worker.py

import asyncio
import logging
from app.utils.supabase_client import supabase
from app.services.pdf_processing import process_pdf_from_row
from app.config import settings

logger = logging.getLogger(__name__)

async def background_pdf_worker():
    logger.info("Starting background PDF worker")
    while True:
        try:
            resp = supabase.table("pdf_files").select("*").order("created_at", desc=True).execute()
            rows = resp.data or []
            for row in rows:
                pdf_id = row.get("id")
                ar = supabase.table("pdf_analysis").select("*").eq("pdf_id", pdf_id).execute()
                if ar.data:
                    continue  # already processed

                # ** Await the async process_pdf_from_row directly **
                await process_pdf_from_row(row)

            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.exception("Worker loop error: %s", e)
            await asyncio.sleep(10)
