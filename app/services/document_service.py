"""
Document upload and management service.
Handles file storage, DB record creation, and triggers the pipeline.
Pipeline runs in the background so the upload response is instant.
"""
import os
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.schemas.document import DocumentUploadMeta, DocumentResponse


def save_uploaded_file(file: UploadFile, document_id: str) -> tuple[str, int]:
    """
    Save PDF to disk using document_id as filename (not original name).
    Returns (file_path, file_size_bytes).
    """
    ext = Path(file.filename).suffix.lower()
    if ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    file_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}{ext}")
    content = file.file.read()

    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, len(content)


def create_document_record(
    meta: DocumentUploadMeta,
    file: UploadFile,
    uploader: User,
    db: Session,
    background_tasks: BackgroundTasks,
) -> DocumentResponse:
    """
    Save file → create DB record → queue pipeline as background task.
    Returns immediately with status=PENDING.
    """
    document_id = str(uuid.uuid4())
    file_path, file_size = save_uploaded_file(file, document_id)

    doc = Document(
        id=document_id,
        university_id=uploader.university_id,
        uploaded_by=uploader.id,
        document_type=meta.document_type,
        department=meta.department,
        semester=meta.semester,
        section=meta.section,
        subject_name=meta.subject_name,
        subject_code=meta.subject_code,
        regulation=meta.regulation,
        academic_year=meta.academic_year,
        original_filename=file.filename,
        file_path=file_path,
        file_size_bytes=file_size,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Queue processing — runs after response is sent
    background_tasks.add_task(run_pipeline_for_document, document_id)

    return DocumentResponse.model_validate(doc)


def run_pipeline_for_document(document_id: str):
    """
    Called in background after upload.
    Creates its own DB session (background tasks run outside request context).
    """
    from app.db.session import SessionLocal
    from app.pipeline.orchestrator import process_document

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        chunk_count = process_document(doc)

        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = chunk_count
        doc.indexed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


def list_documents(university_id: str, db: Session) -> list[DocumentResponse]:
    docs = db.query(Document).filter(
        Document.university_id == university_id
    ).order_by(Document.uploaded_at.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]


def delete_document(document_id: str, university_id: str, db: Session) -> dict:
    """
    Soft-delete: archive in DB + remove from ChromaDB.
    File stays on disk for audit trail.
    """
    from app.services.vector_service import delete_chunks_by_document

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.university_id == university_id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove chunks from ChromaDB
    delete_chunks_by_document(document_id)

    # Soft-delete in PostgreSQL
    doc.status = DocumentStatus.ARCHIVED
    db.commit()

    return {"message": "Document archived and chunks removed"}
