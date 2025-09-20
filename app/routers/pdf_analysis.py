import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

import app.utils.db as db_utils
from app.config import settings
from app.services.log_processing import user_log_processing

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/pdf-analysis")
async def get_pdf_analysis(filename: str = Query(..., description="Name of the PDF file")):
    """
    Retrieve PDF analysis (summary + QA) by PDF filename.
    """
    try:
        if db_utils.db_pool is None:
            logger.error("No db pool configured")
            raise HTTPException(status_code=500, detail=f"DB Pool Not Initialized")

        async with db_utils.db_pool.acquire() as conn:
            pdf_res = await conn.fetchrow(settings.SP_ANALYSIS_FETCH_QUERY, filename)

            if not pdf_res.get("pdf_id"):
                raise HTTPException(status_code=404, detail=f"No PDF found with filename {filename}")

            if not pdf_res.get("summary"):
                raise HTTPException(status_code=404, detail=f"No analysis found for {filename}")


            return {
                "filename": filename,
                "pdf_id": pdf_res.get("pdf_id"),
                "analysis": dict(pdf_res)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF analysis: {str(e)}")

@router.get("/pdf-summary")
async def get_pdf_summary(filename: str = Query(..., description="Name of the PDF file"),
                    user_id: str = "Harman",
                    user_name: str = "harman.jaspaul@gmail.com"):
    """
    Retrieve PDF summary by PDF filename.
    """
    try:
        if db_utils.db_pool is None:
            logger.error("No db pool configured")
            raise HTTPException(status_code=500, detail=f"DB Pool Not Initialized")

        async with db_utils.db_pool.acquire() as conn:
            pdf_res = await conn.fetchrow(settings.SP_SUMMARY_FETCH_QUERY, filename)

            if not pdf_res or not pdf_res.get("pdf_id"):
                raise HTTPException(status_code=404, detail=f"No PDF found with filename {filename}")

            if not pdf_res.get("summary") or len(pdf_res.get("summary")) == 0:
                raise HTTPException(status_code=404, detail=f"No summary found for {filename}")

            log_payload = {
                "user_id": user_id,
                "user_name": user_name,
                "pdf_id": pdf_res.get("pdf_id"),
                "analysis_id": pdf_res.get("analysis_id"),
                "filename": filename,
                "qa_log": [{"timestamp": datetime.now(), "summary": "yes"}],
                "created_at": datetime.now(),
                "modified_at": datetime.now()
            }
            asyncio.create_task(user_log_processing(log_payload))

            return {
                "filename": filename,
                "summary": pdf_res.get("summary")
            }

    except Exception as e:
        logger.exception(f"Error inserting log for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF summary: {str(e)}")


@router.get("/answer")
async def get_pdf_answer(filename: str = Query(..., description="Name of the PDF file"),
                   user_id: str = "Harman",
                   user_name: str = "harman.jaspaul@gmail.com",
                   question: str = ""):
    """
    Retrieve PDF answer by PDF filename and question.
    """
    try:
        if db_utils.db_pool is None:
            logger.error("No db pool configured")
            raise HTTPException(status_code=500, detail=f"DB Pool Not Initialized")

        async with db_utils.db_pool.acquire() as conn:
            pdf_res = await conn.fetchrow(settings.SP_QA_FETCH_QUERY, filename)


        if not pdf_res or not pdf_res.get("pdf_id"):
            raise HTTPException(status_code=404, detail=f"No PDF found with filename {filename}")

        if not pdf_res.get("qa") or len(pdf_res.get("qa")) == 0:
            raise HTTPException(status_code=404, detail=f"No qa found for {filename}")

        qa_res = json.loads(pdf_res.get("qa")) or []
        print(qa_res)

        response: dict = {}
        for qa in qa_res:
            if qa.get("question") == question:
                response = {
                    "filename": filename,
                    "question": question,
                    "answer": qa.get("answer")

                }
                break

        response_default: str = "Question not found."

        #answer: str = ""
        if not response.get("answer"):
            answer = response_default
        else:
            answer = response.get("answer")

        log_payload = {
            "user_id": user_id,
            "user_name": user_name,
            "pdf_id": pdf_res.get("pdf_id"),
            "analysis_id": pdf_res.get("analysis_id"),
            "filename": filename,
            "qa_log": [{
                "timestamp": datetime.now(),
                "question": question,
                "answer": answer}],
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
        asyncio.create_task(user_log_processing(log_payload))

        if not response.get("answer"):
            return response_default
        return response


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF analysis: {str(e)}")

@router.get("/questions")
async def get_pdf_questions(filename: str = Query(..., description="Name of the PDF file")):
    """
    Retrieve PDF answer by PDF filename and question.
    """
    try:
        if db_utils.db_pool is None:
            logger.error("No db pool configured")
            raise HTTPException(status_code=500, detail=f"DB Pool Not Initialized")

        async with db_utils.db_pool.acquire() as conn:
            pdf_res = await conn.fetchrow(settings.SP_QUESTION_FETCH_QUERY, filename)

        if not pdf_res or not pdf_res.get("id"):
            raise HTTPException(status_code=404, detail=f"No PDF found with filename {filename}")

        pdf_questions = pdf_res.get("questions")

        return {
            "filename": filename,
            "questions": json.loads(pdf_questions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF questions: {str(e)}")