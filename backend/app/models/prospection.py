from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProspectionMeta(Base):
    __tablename__ = "prospection_meta"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True)

    status = Column(String(32), nullable=False, default="to_contact")
    owner = Column(String(128), nullable=True)
    notes = Column(String(1024), nullable=True)
    last_contact_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    company = relationship("Company", back_populates="prospect_metas")
    contact = relationship("Contact", back_populates="prospect_metas")
