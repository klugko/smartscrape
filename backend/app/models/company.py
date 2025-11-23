from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    website_url = Column(String(512), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    country = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    industry = Column(String(128), nullable=True)
    size = Column(String(64), nullable=True)
    source_url = Column(String(512), nullable=False)
    tags = Column(String(512), nullable=True)
    prospect_type = Column(String(32), nullable=True)  # "project", "staffing", "both", "unknown"
    score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    prospect_metas = relationship("ProspectionMeta", back_populates="company")
