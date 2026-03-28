"""
University table.
Admin accounts are tied to a university.
All student data, documents, and chunks are scoped by university_id.
This is the root of the entire data isolation guarantee.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class University(Base):
    __tablename__ = "universities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)  # e.g. "amrita_cb"
    city = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="university")
    documents = relationship("Document", back_populates="university")
