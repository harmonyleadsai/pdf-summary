# app/services/pdf_processing.py

from typing import Dict
import logging
import json
from app.utils.pdf import extract_text_from_pdf_bytes
from app.utils.openai_client import call_openai_summary_and_qa  # async version
from app.utils.supabase_client import download_file_to_bytes
from app.config import settings
import app.utils.db as db_utils

logger = logging.getLogger(__name__)

async def process_pdf_from_row(row: Dict) -> None:
    """
    Process one pdf_files row: download, extract, call OpenAI, insert analysis.
    This version is async so we can await call_openai_summary_and_qa.
    """
    pdf_id = row.get("id")
    product_id = row.get("product_id")
    filename = row.get("filename")
    #questions = row.get("questions") or []
    questions = row.get("questions") or []
    path_in_bucket = row.get("storage_url")

    # download bytes
    try:
        if path_in_bucket:
            """import requests
            res = requests.get(storage_url)
            res.raise_for_status()
            pdf_bytes = res.content"""
            pdf_bytes = download_file_to_bytes(path_in_bucket)
        else:
            path = f"{product_id}/{filename}"
            pdf_bytes = download_file_to_bytes(path)
    except Exception as e:
        logger.exception(f"Error downloading PDF for row {pdf_id}: {e}")
        return

    # extract text
    try:
        text = extract_text_from_pdf_bytes(pdf_bytes)
    except Exception as e:
        logger.exception(f"Error extracting text for pdf_id {pdf_id}: {e}")
        return

    # ** Await the async OpenAI call **
    try:
        ai_result = await call_openai_summary_and_qa(text, questions)
    except Exception as e:
        logger.exception(f"Error calling OpenAI for pdf_id {pdf_id}: {e}")
        return

    if not ai_result or not isinstance(ai_result, dict):
        logger.error(f"Invalid OpenAI result for pdf_id {pdf_id}: {ai_result}")
        return

    # prepare summary
    summary = ai_result.get("summary", "")[:10000]  # Trim if too long
    answers = ai_result.get("qa", [])

    #qa_payload = [{"question": q, "answer": next((a["answer"] for an in answers if a["question"] == q), None)} for q in questions]

    analysis_payload = {
        "pdf_id": pdf_id,
        "model_used": settings.OPENAI_MODEL,
        "summary": summary,
        "qa": json.dumps(answers),
    }
    values = list(analysis_payload.values())
    placeholders = ", ".join(f"${i + 1}" for i in range(len(values)))
    query = f"INSERT INTO pdf_analysis (pdf_id, model_used, summary, qa) VALUES ({placeholders}) RETURNING id, pdf_id"

    try:
        if db_utils.db_pool is None:
            logger.error("No db pool configured")
            raise RuntimeError("DB pool not initialized")

        async with db_utils.db_pool.acquire() as conn:
            ins = await conn.fetchrow(query, *values)

            if not ins or not ins.get("pdf_id"):
                logger.error("Failed to insert analysis for pdf_id: %s", pdf_id)
            else:
                logger.info("Inserted analysis for pdf_id %s", pdf_id)
                logger.info("Updating pdf_files for processed flag for pdf_id=%s", pdf_id)
                upd = await conn.execute(
                        "UPDATE pdf_files SET processed=TRUE WHERE id=$1", pdf_id
                    )

                #print("UPD: ", upd)
                if not upd:
                    logger.error("Failed to update pdf_files for flag processed for pdf_id: %s", pdf_id)
                else:
                    logger.info("Updated pdf_files processed flag for pdf_id %s: %s", pdf_id, upd)

    except Exception as e:
        logger.exception(f"Error inserting analysis for pdf_id {pdf_id}: {e}")
