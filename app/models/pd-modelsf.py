from pydantic import BaseModel
from typing import List, Optional

class UploadResponseItem(BaseModel):
    filename: str
    db_row: dict

class UploadResponse(BaseModel):
    uploaded: List[UploadResponseItem]

class HealthStatus(BaseModel):
    status: str = "ok"
