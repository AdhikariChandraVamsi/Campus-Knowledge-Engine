"""
Auth business logic lives here — not in routes.
Routes call these functions. This keeps routes thin and logic testable.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.university import University
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token


def register_user(request: RegisterRequest, db: Session) -> User:
    """
    Validate and create a new user.
    Raises HTTP exceptions for duplicate email or invalid university.
    """
    # Check university exists
    university = db.query(University).filter(
        University.id == request.university_id,
        University.is_active == True,
    ).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found",
        )

    # Check email uniqueness
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        university_id=request.university_id,
        role=request.role,
        department=request.department,
        semester=request.semester,
        section=request.section,
        regulation=request.regulation,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(request: LoginRequest, db: Session) -> TokenResponse:
    """
    Verify credentials and return a JWT.
    The JWT payload embeds context (university_id, role) so routes
    don't need to re-query the DB for basic context.
    """
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Embed context in JWT so every request carries full session info
    token = create_access_token(data={
        "sub": user.id,
        "university_id": user.university_id,
        "role": user.role.value,
        "department": user.department,
        "semester": user.semester,
        "section": user.section,
        "regulation": user.regulation,
    })

    return TokenResponse(
        access_token=token,
        role=user.role.value,
        university_id=user.university_id,
        full_name=user.full_name,
    )
