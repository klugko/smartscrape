from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProspectionMetaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: Optional[int] = None
    contact_id: Optional[int] = None
    status: str
    owner: Optional[str] = None
    notes: Optional[str] = None
    last_contact_date: Optional[datetime] = None


class ProspectionStatusUpdate(BaseModel):
    status: str
    owner: Optional[str] = None
    notes: Optional[str] = None
