from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db_dep
from app.models.prospection import ProspectionMeta
from app.schemas.prospection import ProspectionMetaBase, ProspectionStatusUpdate

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("/", response_model=List[ProspectionMetaBase])
def list_leads(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_dep),
) -> List[ProspectionMetaBase]:
    return (
        db.query(ProspectionMeta)
        .order_by(ProspectionMeta.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@router.patch("/{lead_id}", response_model=ProspectionMetaBase)
def update_lead_status(
    lead_id: int,
    payload: ProspectionStatusUpdate,
    db: Session = Depends(get_db_dep),
) -> ProspectionMetaBase:
    meta = db.get(ProspectionMeta, lead_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    meta.status = payload.status
    if payload.owner is not None:
        meta.owner = payload.owner
    if payload.notes is not None:
        meta.notes = payload.notes
    db.commit()
    db.refresh(meta)
    return meta
