# app/services/background_worker.py

import asyncio
import logging
from app.services.pdf_processing import process_pdf_from_row
from app.config import settings
import app.utils.db as db_utils

logger = logging.getLogger(__name__)

async def background_pdf_worker():
    logger.info("Starting background PDF worker")
    while True:
        try:
            if db_utils.db_pool is None:
                logger.error("No db pool configured")
                raise RuntimeError("DB pool not initialized")

            async with db_utils.db_pool.acquire() as conn:
                rows = await conn.fetch(settings.SP_PDF_FILES_FETCH_QUERY)

                for row in rows:
                    pdf_id = row.get("id")
                    ar = await conn.fetchrow(settings.SP_PDF_ANALYSIS_FETCH_ID_QUERY, pdf_id)

                    if ar:
                        continue  # already processed

                    # ** Await the async process_pdf_from_row directly **
                    await process_pdf_from_row(row)

                await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.exception("Worker loop error: %s", e)
            await asyncio.sleep(10)
