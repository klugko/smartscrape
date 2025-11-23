from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db_dep
from app.models.contact import Contact
from app.schemas.contact import ContactListItem

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/", response_model=List[ContactListItem])
def list_contacts(
    company_id: Optional[int] = None,
    email_contains: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_dep),
) -> List[ContactListItem]:
    query = select(Contact)
    if company_id:
        query = query.where(Contact.company_id == company_id)
    if email_contains:
        query = query.where(Contact.email.ilike(f"%{email_contains}%"))
    query = query.offset(offset).limit(limit)
    return db.execute(query).scalars().all()
