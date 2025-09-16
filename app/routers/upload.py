from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import json
from uuid import UUID
import logging
from app.config import settings
from app.utils.supabase_client import upload_file, get_public_url, supabase
from app.services.pdf_processing import process_pdf_from_row  # maybe used later

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
        qobj = json.loads(questions_json)
    except Exception:
        raise HTTPException(status_code=400, detail="questions_json must be valid JSON")

    results = []
    for file in files:
        filename = file.filename
        content_type = file.content_type or "application/pdf"
        body = await file.read()
        path_in_bucket = f"{product_id}/{filename}"

        try:
            upload_res = upload_file(path_in_bucket, body, content_type)
        except Exception as e:
            logger.exception("Upload failed")
            raise HTTPException(status_code=500, detail=f"Upload to storage failed: {e}")

        if settings.ALLOWED_BUCKET_PUBLIC:
            storage_url = get_public_url(path_in_bucket)
        else:
            sign = supabase.storage().from_(settings.SUPABASE_BUCKET).create_signed_url(path_in_bucket, 60 * 60)
            storage_url = sign.get("signedURL") if isinstance(sign, dict) else sign

        if isinstance(qobj, dict):
            questions_for_file = qobj.get(filename, [])
        elif isinstance(qobj, list):
            questions_for_file = qobj
        else:
            questions_for_file = []

        insert_payload = {
            "product_id": product_id,
            "filename": filename,
            "mime_type": content_type,
            "file_size": len(body),
            "storage_url": storage_url,
            "questions": json.dumps(questions_for_file),
        }
        resp = supabase.table("pdf_files").insert(insert_payload).execute()
        print("Fetched data:", resp.data[0])
        if not getattr(resp, "data", None) or not isinstance(resp.data, list) or len(resp.data) == 0:
            logger.error("Supabase insert response: %s", resp.json())
            raise HTTPException(status_code=500, detail="Failed to insert metadata into pdf_files")
        inserted = resp.data[0] if isinstance(resp.data, list) and resp.data else resp.data
        results.append({"filename": filename, "db_row": inserted})

    return {"uploaded": results}
