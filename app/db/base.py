"""
Declarative base for all SQLAlchemy models.
All models import Base from here — this gives Alembic a single
place to discover all tables for migrations.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic sees them during autogenerate
# (add new model imports here as you create them)
from app.models import university, user, document, query_log  # noqa: F401, E402
