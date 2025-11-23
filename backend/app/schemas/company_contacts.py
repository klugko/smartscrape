from typing import List

from pydantic import BaseModel, ConfigDict

from .company import CompanyDetail
from .contact import ContactListItem
from .prospection import ProspectionMetaBase


class CompanyWithContacts(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company: CompanyDetail
    contacts: List[ContactListItem]
    leads: List[ProspectionMetaBase]


class CompanyContactsSearchResponse(BaseModel):
    total: int
    items: List[CompanyWithContacts]
