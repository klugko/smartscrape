from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.api.deps import get_db_dep
from app.models.company import Company
from app.models.prospection import ProspectionMeta
from app.schemas.company import CompanyListItem, CompanyDetail, CompanyFilter

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=List[CompanyListItem])
def list_companies(
    country: Optional[str] = None,
    prospect_type: Optional[str] = None,
    min_score: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_dep),
) -> List[CompanyListItem]:
    query = select(Company)

    conditions = []
    if country:
        conditions.append(Company.country == country)
    if prospect_type:
        conditions.append(Company.prospect_type == prospect_type)
    if min_score is not None:
        conditions.append(Company.score >= min_score)

    if status:
        query = query.join(ProspectionMeta, ProspectionMeta.company_id == Company.id)
        conditions.append(ProspectionMeta.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.offset(offset).limit(limit)
    results = db.execute(query).scalars().all()
    return results

@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: int, db: Session = Depends(get_db_dep)) -> CompanyDetail:
    company = db.get(Company, company_id)
    return company
