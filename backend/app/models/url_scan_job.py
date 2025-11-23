from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base import Base

class UrlScanJob(Base):
    __tablename__ = "url_scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    input_url = Column(String(512), nullable=False)
    normalized_root_url = Column(String(512), nullable=False, index=True)

    status = Column(String(32), nullable=False, default="pending")  # pending, running, done, error
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
