import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.logging import setup_logging
from app.core.config import get_settings
from app.db.session import engine
from app.db.base import Base

from app.api.routes import jobs, companies, contacts, leads, company_contacts

logger = logging.getLogger("app.main")


def wait_for_db(max_attempts: int = 10, delay: float = 2.0) -> None:
    """
    Attend que la base de données soit disponible avant de continuer.
    Lève une RuntimeError si la DB reste inaccessible après max_attempts.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                logger.info(
                    "Database is available (attempt %s/%s).",
                    attempt,
                    max_attempts,
                )
                return
        except OperationalError as exc:
            logger.warning(
                "Database not ready (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(delay)

    logger.error("Database not available after %s attempts.", max_attempts)
    raise RuntimeError("Database not available after several attempts.")


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()  

    wait_for_db()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="SmartScrape",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jobs.router, prefix="/api")
    app.include_router(companies.router, prefix="/api")
    app.include_router(contacts.router, prefix="/api")
    app.include_router(leads.router, prefix="/api")
    app.include_router(company_contacts.router, prefix="/api")

    logger.info("SmartScrape API initialized")
    return app


app = create_app()
