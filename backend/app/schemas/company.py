from typing import Optional

from pydantic import BaseModel, ConfigDict

from .common import Timestamped


class CompanyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    website_url: str
    description: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    source_url: str
    tags: Optional[str] = None
    prospect_type: Optional[str] = None
    score: Optional[float] = None


class CompanyListItem(CompanyBase, Timestamped):
    pass


class CompanyDetail(CompanyBase, Timestamped):
    pass


class CompanyFilter(BaseModel):
    country: Optional[str] = None
    prospect_type: Optional[str] = None
    min_score: Optional[float] = None
    status: Optional[str] = None  
    limit: int = 50
    offset: int = 0
