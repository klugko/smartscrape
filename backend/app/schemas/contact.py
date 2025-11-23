from typing import Optional

from pydantic import BaseModel, ConfigDict

from .common import Timestamped


class ContactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    full_name: Optional[str] = None
    role_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_decision_maker: bool
    source_page_url: Optional[str] = None


class ContactListItem(ContactBase, Timestamped):
    pass
