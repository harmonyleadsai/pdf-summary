# app/services/pdf_processing.py

from typing import Dict, List
import logging

from app.utils.pdf import extract_text_from_pdf_bytes
from app.utils.openai_client import call_openai_summary_and_qa  # async version
from app.utils.supabase_client import download_file_to_bytes, supabase
from app.config import settings

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
    storage_url = row.get("storage_url")

    # download bytes
    try:
        if storage_url:
            import requests
            res = requests.get(storage_url)
            res.raise_for_status()
            pdf_bytes = res.content
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

    #qa_payload = [{"question": q, "answer": next((a["answer"] for a in answers if a["question"] == q), None)} for q in questions]

    analysis_payload = {
        "pdf_id": pdf_id,
        "model_used": settings.OPENAI_MODEL,
        "summary": summary,
        "qa": answers,
    }

    try:
        ins = supabase.table("pdf_analysis").insert(analysis_payload).execute()
        if not getattr(ins, "data", None) or not isinstance(ins.data, list) or len(ins.data) == 0:
            logger.error("Failed to insert analysis for pdf_id %s: %s", pdf_id, ins.json())
        else:
            logger.info("Inserted analysis for pdf_id %s", pdf_id)
    except Exception as e:
        logger.exception(f"Error inserting analysis for pdf_id {pdf_id}: {e}")
