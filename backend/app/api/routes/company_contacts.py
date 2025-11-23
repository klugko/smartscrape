from typing import List, Optional, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db_dep
from app.models.company import Company
from app.models.contact import Contact
from app.models.prospection import ProspectionMeta
from app.schemas.company_contacts import (
    CompanyWithContacts,
    CompanyContactsSearchResponse,
)
from app.schemas.company import CompanyDetail
from app.schemas.contact import ContactListItem
from app.schemas.prospection import ProspectionMetaBase

router = APIRouter(prefix="/company-contacts", tags=["company-contacts"])


@router.get("/search", response_model=CompanyContactsSearchResponse)
def search_company_contacts(
    q: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    prospect_type: Optional[str] = None,
    min_score: Optional[float] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db_dep),
) -> CompanyContactsSearchResponse:
    """
    Recherche agrégée entreprises + contacts + leads avec filtres et pagination.

    - q : recherche texte sur (company.name, description, tags, website_url,
          contact.full_name, role_title, email)
    - country, city, industry : filtres de base société
    - prospect_type : project|staffing|both|unknown
    - min_score : score minimal (0-100)
    - status : statut de prospection (ProspectionMeta.status)
    - page / page_size : pagination (1-based)
    """

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 200:
        page_size = 200

    # ---- requête de base sur Company.id avec jointures ----
    base_query = (
        db.query(Company.id)
        .outerjoin(Contact, Contact.company_id == Company.id)
        .outerjoin(ProspectionMeta, ProspectionMeta.company_id == Company.id)
    )

    conditions = []

    if country:
        conditions.append(Company.country == country)
    if city:
        conditions.append(Company.city == city)
    if industry:
        conditions.append(Company.industry == industry)
    if prospect_type:
        conditions.append(Company.prospect_type == prospect_type)
    if min_score is not None:
        conditions.append(Company.score >= min_score)
    if status:
        conditions.append(ProspectionMeta.status == status)

    if q:
        pattern = f"%{q}%"
        conditions.append(
            or_(
                Company.name.ilike(pattern),
                Company.description.ilike(pattern),
                Company.website_url.ilike(pattern),
                Company.tags.ilike(pattern),
                Contact.full_name.ilike(pattern),
                Contact.role_title.ilike(pattern),
                Contact.email.ilike(pattern),
            )
        )

    if conditions:
        base_query = base_query.filter(and_(*conditions))

    # ---- Total distinct de companies correspondant aux filtres ----
    # subquery distinct pour éviter les doublons liés aux contacts/leads.
    filtered_ids_subq = base_query.distinct().subquery()
    total = db.query(func.count()).select_from(filtered_ids_subq).scalar() or 0

    if total == 0:
        return CompanyContactsSearchResponse(total=0, items=[])

    # ---- Pagination sur les IDs ----
    offset = (page - 1) * page_size

    paged_ids_rows = (
        db.query(filtered_ids_subq.c.id)
        .order_by(filtered_ids_subq.c.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )
    company_ids = [row[0] for row in paged_ids_rows]

    if not company_ids:
        return CompanyContactsSearchResponse(total=total, items=[])

    # ---- Charger les Company + relations (contacts + prospection_meta) ----
    companies: List[Company] = (
        db.query(Company)
        .options(
            selectinload(Company.contacts),
            selectinload(Company.prospect_metas),
        )
        .filter(Company.id.in_(company_ids))
        .all()
    )

    # remet les companies dans l'ordre de company_ids
    company_by_id: Dict[int, Company] = {c.id: c for c in companies}
    ordered_companies = [company_by_id[cid] for cid in company_ids if cid in company_by_id]

    # ---- Mapper vers la réponse Pydantic ----
    items: List[CompanyWithContacts] = []

    for company in ordered_companies:
        company_schema = CompanyDetail.from_orm(company)
        contacts_schema = [
            ContactListItem.from_orm(contact) for contact in company.contacts
        ]
        leads_schema = [
            ProspectionMetaBase.from_orm(meta) for meta in company.prospect_metas
        ]

        items.append(
            CompanyWithContacts(
                company=company_schema,
                contacts=contacts_schema,
                leads=leads_schema,
            )
        )

    return CompanyContactsSearchResponse(total=total, items=items)
