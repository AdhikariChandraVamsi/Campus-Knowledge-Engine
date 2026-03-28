"""Document upload and management endpoints (admin only)."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app.schemas.document import DocumentUploadMeta, DocumentResponse
from app.services.document_service import (
    create_document_record,
    list_documents,
    delete_document,
)
from app.core.dependencies import require_admin, get_current_user
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    department: str = Form(...),
    semester: str = Form(None),
    section: str = Form(None),
    subject_name: str = Form(None),
    subject_code: str = Form(None),
    regulation: str = Form(None),
    academic_year: str = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Upload a PDF document with metadata as individual form fields.
    Processing happens in background — response returns immediately with status=pending.
    """
    try:
        upload_meta = DocumentUploadMeta(
            document_type=document_type,
            department=department,
            semester=semester,
            section=section,
            subject_name=subject_name,
            subject_code=subject_code,
            regulation=regulation,
            academic_year=academic_year,
        )
    except Exception as e:
        return JSONResponse(status_code=422, content={"detail": f"Invalid metadata: {e}"})

    return create_document_record(upload_meta, file, admin, db, background_tasks)


@router.get("/", response_model=list[DocumentResponse])
def list_university_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents for the current user's university."""
    return list_documents(current_user.university_id, db)


@router.delete("/{document_id}")
def archive_document(
    document_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Archive a document and remove its chunks from ChromaDB."""
    return delete_document(document_id, admin.university_id, db)
