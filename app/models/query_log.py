"""
Query log — every student query is recorded.
Unanswered queries are flagged for admin review.
This is the feedback loop that tells admins what documents are missing.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)

    # Was the query answered or did it fall below similarity threshold?
    was_answered = Column(Boolean, default=True)
    top_similarity_score = Column(Float, nullable=True)

    # Context used for retrieval
    department = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    section = Column(String, nullable=True)
    document_type = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="query_logs")
