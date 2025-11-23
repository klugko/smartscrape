from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class UrlScanRequest(BaseModel):
    """Payload de création de jobs de scan d'URL."""
    urls: List[HttpUrl]


class UrlScanJobBase(BaseModel):
    """Représentation d'un job de scan côté API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_url: str
    normalized_root_url: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
