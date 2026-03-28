"""
Document table — one row per uploaded PDF.
Every chunk in ChromaDB has a document_id that points here.
Deleting a document here triggers chunk cleanup in ChromaDB.
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Enum, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"       # Uploaded, not yet processed
    PROCESSING = "processing" # Pipeline running
    INDEXED = "indexed"       # In ChromaDB, ready for queries
    FAILED = "failed"         # Pipeline errored
    ARCHIVED = "archived"     # Soft-deleted


class DocumentType(str, enum.Enum):
    SYLLABUS = "syllabus"
    TIMETABLE = "timetable"
    PYQ = "pyq"               # Previous Year Questions
    CO_PO = "co_po"
    EVALUATION = "evaluation"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Document metadata — these become ChromaDB filter fields
    document_type = Column(Enum(DocumentType), nullable=False)
    department = Column(String, nullable=False)   # "CSE"
    semester = Column(String, nullable=True)       # "5"
    section = Column(String, nullable=True)        # "F"
    subject_name = Column(String, nullable=True)
    subject_code = Column(String, nullable=True)
    regulation = Column(String, nullable=True)     # "2023"
    academic_year = Column(String, nullable=True)  # "2024-25"

    # File info
    original_filename = Column(String, nullable=False)
    file_path = Column(Text, nullable=False)       # Path on disk
    file_size_bytes = Column(Integer, nullable=True)

    # Processing state
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    chunk_count = Column(Integer, default=0)       # How many chunks were created
    error_message = Column(Text, nullable=True)    # If status=FAILED, why

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    university = relationship("University", back_populates="documents")
