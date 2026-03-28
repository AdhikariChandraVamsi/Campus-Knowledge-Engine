"""
User table — covers both students and admins.
Role field distinguishes them. University_id scopes all data access.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    university_id = Column(String, ForeignKey("universities.id"), nullable=False)

    # Auth fields
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)

    # Profile fields (students)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=True)   # e.g. "CSE"
    semester = Column(String, nullable=True)      # e.g. "5"
    section = Column(String, nullable=True)       # e.g. "F"
    regulation = Column(String, nullable=True)    # e.g. "2023"

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    university = relationship("University", back_populates="users")
    query_logs = relationship("QueryLog", back_populates="user")
