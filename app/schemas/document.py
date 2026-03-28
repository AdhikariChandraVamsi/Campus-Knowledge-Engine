"""
Document upload and response schemas.
The upload schema captures all metadata the admin must provide.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.document import DocumentType, DocumentStatus


class DocumentUploadMeta(BaseModel):
    """Metadata submitted alongside the PDF file."""
    document_type: DocumentType
    department: str
    semester: Optional[str] = None
    section: Optional[str] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    regulation: Optional[str] = None
    academic_year: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    university_id: str
    document_type: str
    department: str
    semester: Optional[str]
    section: Optional[str]
    subject_name: Optional[str]
    original_filename: str
    status: str
    chunk_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
