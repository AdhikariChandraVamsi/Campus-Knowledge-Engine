"""
SQLAlchemy engine and session factory.
`get_db` is used as a FastAPI dependency — it yields a session per request
and guarantees cleanup even if the request fails.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Detect stale connections
    pool_size=10,             # Connection pool size
    max_overflow=20,          # Extra connections under load
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency. Use as:
        db: Session = Depends(get_db)
    Automatically closes session after request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
