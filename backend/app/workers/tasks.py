from __future__ import annotations

from datetime import datetime
import logging
from typing import List

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.url_scan_job import UrlScanJob
from app.models.company import Company
from app.models.contact import Contact
from app.models.prospection import ProspectionMeta
from app.services.scraping import crawl_site, normalize_root_url, PageContent
from app.services.parsing import (
    extract_contacts_from_page,
    extract_emails,
    detect_signals_from_text,
)
from app.services.classification import classify_prospect
from app.services.ai_enrichment import enrich_company_with_llm

settings = get_settings()
logger = logging.getLogger(__name__)

redis_conn = Redis.from_url(settings.REDIS_URL)
url_scan_queue = Queue("url_scan", connection=redis_conn)


def enqueue_url_scan_job(job_id: int) -> None:
    url_scan_queue.enqueue(process_url_scan_job, job_id, job_timeout=900)


def process_url_scan_job(job_id: int) -> None:
    db: Session = SessionLocal()
    try:
        job = db.get(UrlScanJob, job_id)
        if not job:
            logger.error("UrlScanJob %s not found", job_id)
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        db.refresh(job)

        pages: List[PageContent] = crawl_site(job.normalized_root_url)
        if not pages:
            job.status = "error"
            job.error_message = "No pages crawled"
            job.finished_at = datetime.utcnow()
            db.commit()
            return

        # ---- Agrégation du texte pour l'analyse globale ----
        pages_html = [p.html for p in pages]
        full_text = " ".join(pages_html)

        # Signaux heuristiques de base
        signals = detect_signals_from_text(full_text)
        prospect_type_heur, score_heur = classify_prospect(signals)

        # ---- Extraction heuristique d'infos société (fallback) ----
        from app.services.parsing import extract_company_info_from_pages

        company_info = extract_company_info_from_pages(pages_html)

        # ---- Enrichissement IA (classification + profil société) ----
        ai_enrichment = enrich_company_with_llm(
            root_url=job.normalized_root_url,
            text=full_text,
            signals=signals,
        )

        # ---- Upsert Company ----
        company = (
            db.query(Company)
            .filter(Company.website_url == job.normalized_root_url)
            .one_or_none()
        )
        if not company:
            company = Company(
                website_url=job.normalized_root_url,
                source_url=job.input_url,
            )

        # Nom + description
        if ai_enrichment and ai_enrichment.name:
            company.name = ai_enrichment.name[:255]
        elif company_info.name and not company.name:
            company.name = company_info.name[:255]

        if ai_enrichment and ai_enrichment.description:
            company.description = ai_enrichment.description[:1024]
        elif company_info.description and not company.description:
            company.description = company_info.description[:1024]

        # Localisation / industry / taille
        if ai_enrichment:
            if ai_enrichment.country:
                company.country = ai_enrichment.country[:128]
            if ai_enrichment.city:
                company.city = ai_enrichment.city[:128]
            if ai_enrichment.industry:
                company.industry = ai_enrichment.industry[:128]
            if ai_enrichment.size:
                company.size = ai_enrichment.size[:64]

            if ai_enrichment.tags:
                # Stockage simple CSV, exploitable côté client
                tags_str = ", ".join(ai_enrichment.tags[:10])
                company.tags = tags_str[:512]

        # Type de prospect + score
        if ai_enrichment and ai_enrichment.prospect_type:
            company.prospect_type = ai_enrichment.prospect_type
        else:
            company.prospect_type = prospect_type_heur

        if ai_enrichment and ai_enrichment.score is not None:
            company.score = ai_enrichment.score
        else:
            company.score = score_heur

        db.add(company)
        db.commit()
        db.refresh(company)

        # ---- Extraction des contacts (heuristique) ----
        existing_emails = {
            c.email
            for c in db.query(Contact).filter(Contact.company_id == company.id)
            if c.email
        }

        for page in pages:
            contacts = extract_contacts_from_page(page.url, page.html)
            for parsed in contacts:
                if not parsed.email or parsed.email in existing_emails:
                    continue

                contact = Contact(
                    company_id=company.id,
                    full_name=parsed.full_name,
                    role_title=parsed.role_title,
                    email=parsed.email,
                    phone=parsed.phone,
                    linkedin_url=parsed.linkedin_url,
                    is_decision_maker=False,  # TODO  à affiner
                    source_page_url=page.url,
                )
                db.add(contact)
                db.flush()
                existing_emails.add(parsed.email)

                meta = ProspectionMeta(
                    company_id=company.id,
                    contact_id=contact.id,
                    status="to_contact",
                )
                db.add(meta)

        job.status = "done"
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        logger.exception("Error processing UrlScanJob %s: %s", job_id, exc)
        job = db.get(UrlScanJob, job_id)
        if job:
            job.status = "error"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
