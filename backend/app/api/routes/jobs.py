from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db_dep
from app.models.url_scan_job import UrlScanJob
from app.schemas.url_scan_job import UrlScanRequest, UrlScanJobBase
from app.services.scraping import normalize_root_url
from app.workers.tasks import enqueue_url_scan_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/scan-urls", response_model=List[UrlScanJobBase])
def create_scan_jobs(
    payload: UrlScanRequest,
    db: Session = Depends(get_db_dep),
) -> List[UrlScanJobBase]:
    jobs: List[UrlScanJob] = []
    for url in payload.urls:
        root = normalize_root_url(str(url))
        job = UrlScanJob(
            input_url=str(url),
            normalized_root_url=root,
            status="pending",
        )
        db.add(job)
        db.flush()
        jobs.append(job)
    db.commit()

    for job in jobs:
        enqueue_url_scan_job(job.id)

    return jobs

@router.get("/{job_id}", response_model=UrlScanJobBase)
def get_job(job_id: int, db: Session = Depends(get_db_dep)) -> UrlScanJobBase:
    job = db.get(UrlScanJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
