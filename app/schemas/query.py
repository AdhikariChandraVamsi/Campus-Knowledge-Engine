"""
Query request and response schemas.
The request carries the question + optional context overrides.
The response includes the answer and what chunks were used (for transparency).
"""
from pydantic import BaseModel
from typing import Optional, List


class QueryRequest(BaseModel):
    question: str
    # Optional overrides — if student provides these, they override session defaults
    department: Optional[str] = None
    semester: Optional[str] = None
    section: Optional[str] = None
    document_type: Optional[str] = None


class ChunkReference(BaseModel):
    """Which chunk contributed to this answer — for traceability."""
    chunk_id: str
    similarity_score: float
    document_type: str


class QueryResponse(BaseModel):
    answer: str
    was_answered: bool
    chunks_used: List[ChunkReference] = []
    clarification_needed: Optional[str] = None  # If context is incomplete
