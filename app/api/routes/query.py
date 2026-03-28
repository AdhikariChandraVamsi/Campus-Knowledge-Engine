"""Student query endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import process_student_query
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a question. The system:
    1. Resolves context from your profile
    2. Checks for missing required fields (may return clarification_needed)
    3. Retrieves relevant chunks from your university's documents
    4. Generates a grounded answer
    """
    return process_student_query(request, current_user, db)
