import json
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.config import settings
from app.utils.supabase_client import upload_file, get_public_url, supabase
#from app.utils.db import db_pool
import app.utils.db as db_utils

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload/")
async def upload_pdfs(
    product_id: str = Form(...),
    questions_json: str = Form(...),
    files: List[UploadFile] = File(...),
):
    try:
        _ = UUID(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="product_id must be a UUID string")
    try:
        question_obj = json.loads(questions_json)
    except Exception:
        raise HTTPException(status_code=400, detail="questions_json must be valid JSON")

    results = []
    for file in files:
        filename = file.filename
        content_type = file.content_type or "application/pdf"
        body = await file.read()
        path_in_bucket = f"{product_id}/{filename}"

        try:
            upload_file(path_in_bucket, body, content_type)
        except Exception as e:
            logger.exception("Upload failed")
            raise HTTPException(status_code=500, detail=f"Upload to storage failed: {e}")

        """if settings.ALLOWED_BUCKET_PUBLIC:
            storage_url = get_public_url(path_in_bucket)
        else:
            sign = supabase.storage().from_(settings.SUPABASE_BUCKET).create_signed_url(path_in_bucket, 60 * 60)
            storage_url = sign.get("signedURL") if isinstance(sign, dict) else sign
        """

        if isinstance(question_obj, dict):
            questions_for_file = question_obj.get(filename, [])
        elif isinstance(question_obj, list):
            questions_for_file = question_obj
        else:
            questions_for_file = []

        insert_payload = {
            "product_id": product_id,
            "filename": filename,
            "mime_type": content_type,
            "file_size": len(body),
            "storage_url": path_in_bucket,
            "questions": json.dumps(questions_for_file),
        }

        values = list(insert_payload.values())
        columns = ", ".join(insert_payload.keys())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(values)))
        query = f"INSERT INTO pdf_files ({columns}) VALUES ({placeholders}) RETURNING id, filename"

        try:
            if db_utils.db_pool is None:
                logger.error("No db pool configured")
                raise RuntimeError("DB pool not initialized")

            async with db_utils.db_pool.acquire() as conn:
                ins = await conn.fetchrow(query, *values)

                #print("Ins: ", ins)
                if not ins or len(ins.get("filename")) == 0:
                    logger.error("Failed to insert into pdf_files for filename: %s", filename)
                    results.append({"filename": filename, "status": "failed"})
                    #raise HTTPException(status_code=500, detail="Failed to insert metadata into pdf_files")
                else:
                    logger.info("Inserted into pdf_files for filename %s", filename)
                    results.append({"filename": filename, "status": "inserted"})

        except Exception as e:
            logger.exception(f"Error inserting analysis for id {id}: {e}")
            results.append({"filename": filename, "status": "failed"})

    return {"uploaded": results}

