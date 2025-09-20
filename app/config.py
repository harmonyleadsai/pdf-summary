import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""
    ALLOWED_BUCKET_PUBLIC: bool = False
    POLL_INTERVAL_SECONDS: int = 15
    SUPABASE_DB_DSN: str = ""
    SUPABASE_DB_MIN_SIZE: int = 1
    SUPABASE_DB_MAX_SIZE: int = 5
    SP_PDF_FILES_FETCH_QUERY: str = "SELECT id, product_id, filename, mime_type, file_size, storage_url, created_at, questions FROM pdf_files WHERE processed is FALSE order by created_at desc"
    SP_PDF_ANALYSIS_FETCH_ID_QUERY: str = "SELECT id FROM pdf_analysis WHERE pdf_id="
    SP_ANALYSIS_FETCH_QUERY: str = "SELECT pdf_id, filename, storage_url, summary, qa FROM product_with_pdfs WHERE filename=$1 LIMIT 1"
    SP_SUMMARY_FETCH_QUERY: str
    SP_QA_FETCH_QUERY: str
    SP_QUESTION_FETCH_QUERY: str
    SP_USER_LOG_FETCH_QUERY: str
    SP_UPDATE_USER_LOG_QUERY: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
