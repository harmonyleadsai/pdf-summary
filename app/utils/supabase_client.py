import os
import requests
from supabase import create_client
from app.config import settings
import tempfile
import logging

logger = logging.getLogger(__name__)

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_file(path_in_bucket: str, file_bytes: bytes, content_type: str):
    storage = supabase.storage
    #file_obj = io.BytesIO(file_bytes)
    file_options = {"content-type": content_type}
    tmp_dir = None
    tmp_path = None

    try:
        # Make a temporary directory
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_path = os.path.join(tmp_dir.name, os.path.basename(path_in_bucket))
        # Write bytes to a file in that directory
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)
            f.flush()
        # Now reopen in read-binary mode and pass file to supabase upload
        with open(tmp_path, "rb") as f_read:
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=path_in_bucket,
                file=f_read,
                file_options=file_options
            )
        return res
    except Exception as e:
        raise e
    finally:
        # cleanup
        if tmp_dir:
            tmp_dir.cleanup()

def get_public_url(path_in_bucket: str) -> str:
    storage = supabase.storage
    url = storage.from_(settings.SUPABASE_BUCKET).get_public_url(path_in_bucket)
    if isinstance(url, dict):
        return url.get("publicURL") or url.get("public_url") or ""
    return url

def download_file_to_bytes(path_in_bucket: str) -> bytes:
    storage = supabase.storage
    data = storage.from_(settings.SUPABASE_BUCKET).download(path_in_bucket)
    if isinstance(data, bytes):
        return data
    try:
        return data.read()

    except Exception:
        signed = storage.from_(settings.SUPABASE_BUCKET).create_signed_url(path_in_bucket, 60)
        signed_url = signed.get("signedURL") if isinstance(signed, dict) else signed
        if not signed_url:
            raise RuntimeError("Unable to download file from supabase storage and couldn't create signed URL.")
        r = requests.get(signed_url)
        r.raise_for_status()
        return r.content
