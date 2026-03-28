"""
Auth request/response schemas.
Pydantic validates incoming JSON and shapes outgoing responses.
The response schemas never expose hashed_password.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    university_id: str
    role: UserRole = UserRole.STUDENT

    # Student-only optional fields
    department: Optional[str] = None
    semester: Optional[str] = None
    section: Optional[str] = None
    regulation: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    university_id: str
    full_name: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    university_id: str
    department: Optional[str]
    semester: Optional[str]
    section: Optional[str]
    regulation: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}
