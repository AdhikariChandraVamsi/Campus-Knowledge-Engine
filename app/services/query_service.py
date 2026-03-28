"""
Query orchestration service.
This is the core of the chatbot — it ties together:
context resolution → retrieval → threshold check → LLM → logging
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.query_log import QueryLog
from app.schemas.query import QueryRequest, QueryResponse, ChunkReference
from app.services.vector_service import query_chunks
from app.services.llm_service import generate_answer
from app.core.config import settings


def resolve_query_context(request: QueryRequest, user: User) -> dict:
    """
    Context Resolution Engine (as per architecture doc):
    - If query provides explicit values → use them
    - Else → fallback to student profile values from JWT/DB
    Returns the filter dict for ChromaDB.
    """
    return {
        "dept": request.department or user.department,
        "semester": request.semester or user.semester,
        "section": request.section or user.section,
        "document_type": request.document_type,
    }


def check_missing_context(filters: dict, query: str) -> str | None:
    """
    Intent validation — detect if critical fields are missing.
    For timetable queries, section is required.
    Returns a clarification question if something critical is missing, else None.
    """
    query_lower = query.lower()
    timetable_keywords = ["timetable", "schedule", "class", "monday", "tuesday",
                          "wednesday", "thursday", "friday", "slot", "timing"]

    is_timetable_query = any(kw in query_lower for kw in timetable_keywords)

    if is_timetable_query and not filters.get("section"):
        return "Which section are you in? (e.g., A, B, C, D, E, F)"

    return None


def process_student_query(
    request: QueryRequest,
    user: User,
    db: Session,
) -> QueryResponse:
    """
    Full query pipeline:
    1. Resolve context from user profile + request overrides
    2. Check for missing critical fields (clarification)
    3. Query ChromaDB with university isolation
    4. Check similarity threshold
    5. Generate LLM answer
    6. Log the query
    """
    # Step 1: Context resolution
    filters = resolve_query_context(request, user)

    # Step 2: Clarification check
    clarification = check_missing_context(filters, request.question)
    if clarification:
        return QueryResponse(
            answer="",
            was_answered=False,
            clarification_needed=clarification,
        )

    # Step 3: Retrieve chunks (always scoped to student's university)
    is_timetable = filters.get("document_type") == "timetable" or "timetable" in request.question.lower()
    
    exact_where = None
    k_results = 5
    if is_timetable:
        k_results = 4
        # Apply strict metadata pre-filter as requested
        # We ensure university_id remains isolated structurally securely.
        exact_where = {
            "$and": [
                {"dept": {"$eq": filters.get("dept")}},
                {"semester": {"$eq": filters.get("semester")}},
                {"section": {"$eq": filters.get("section")}},
                {"university_id": {"$eq": user.university_id}}
            ]
        }

    retrieved = query_chunks(
        query_text=request.question,
        university_id=user.university_id,
        filters={k: v for k, v in filters.items() if v},
        n_results=k_results,
        exact_where=exact_where,
    )

    # Step 4: Similarity threshold check
    # Chunks below threshold are treated as "no relevant data"
    above_threshold = [
        c for c in retrieved
        if c["similarity_score"] >= settings.SIMILARITY_THRESHOLD
    ]

    was_answered = len(above_threshold) > 0

    # Step 5: Generate answer
    if was_answered:
        answer = generate_answer(request.question, above_threshold)
    else:
        answer = (
            "I don't have information about this in the uploaded documents. "
            "Please contact your class advisor or check the university portal."
        )

    # Step 6: Log the query
    top_score = retrieved[0]["similarity_score"] if retrieved else None
    log = QueryLog(
        university_id=user.university_id,
        user_id=user.id,
        query_text=request.question,
        answer_text=answer,
        was_answered=was_answered,
        top_similarity_score=top_score,
        department=filters.get("dept"),
        semester=filters.get("semester"),
        section=filters.get("section"),
        document_type=filters.get("document_type"),
    )
    db.add(log)
    db.commit()

    chunk_refs = [
        ChunkReference(
            chunk_id=c["chunk_id"],
            similarity_score=c["similarity_score"],
            document_type=c["metadata"].get("document_type", "unknown"),
        )
        for c in above_threshold
    ]

    return QueryResponse(
        answer=answer,
        was_answered=was_answered,
        chunks_used=chunk_refs,
    )
