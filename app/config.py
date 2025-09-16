import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "pdfs"
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    ALLOWED_BUCKET_PUBLIC: bool = Field(False, env="ALLOWED_BUCKET_PUBLIC")
    POLL_INTERVAL_SECONDS: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = True
		
settings = Settings()