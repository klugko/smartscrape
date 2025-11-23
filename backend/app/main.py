import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.config import get_settings
from app.db.session import engine
from app.db.base import Base

from app.api.routes import jobs, companies, contacts, leads, company_contacts

def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
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

    logging.getLogger(__name__).info("SmartScrape API initialized")
    return app

app = create_app()
