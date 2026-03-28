"""
Test configuration.
Uses SQLite in-memory so tests never touch real PostgreSQL.
DB is created ONCE per session — fixtures that need a university
reuse the same one created at session scope.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db

SQLITE_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once for the entire test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(setup_db):
    """Single TestClient reused across all tests in the session."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def seeded_university(client):
    """Create a university ONCE for the entire test session."""
    r = client.post("/universities/", json={
        "name": "Test University",
        "slug": "test_uni",
        "city": "Chennai",
    })
    assert r.status_code == 201, f"University seed failed: {r.text}"
    return r.json()


@pytest.fixture(scope="session")
def admin_token(client, seeded_university):
    """Register an admin and return JWT — once per session."""
    client.post("/auth/register", json={
        "full_name": "Test Admin",
        "email": "testadmin@uni.edu",
        "password": "Admin@1234",
        "university_id": seeded_university["id"],
        "role": "admin",
    })
    r = client.post("/auth/login", json={
        "email": "testadmin@uni.edu",
        "password": "Admin@1234",
    })
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def student_token(client, seeded_university):
    """Register a student and return JWT — once per session."""
    client.post("/auth/register", json={
        "full_name": "Test Student",
        "email": "teststudent@uni.edu",
        "password": "Student@1234",
        "university_id": seeded_university["id"],
        "role": "student",
        "department": "CSE",
        "semester": "5",
        "section": "F",
    })
    r = client.post("/auth/login", json={
        "email": "teststudent@uni.edu",
        "password": "Student@1234",
    })
    assert r.status_code == 200
    return r.json()["access_token"]
