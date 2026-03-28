"""Auth endpoint tests."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_register_student(client, seeded_university):
    r = client.post("/auth/register", json={
        "full_name": "Vamsi Test",
        "email": "vamsi@test.edu",
        "password": "Test@1234",
        "university_id": seeded_university["id"],
        "role": "student",
        "department": "CSE",
        "semester": "5",
        "section": "F",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "vamsi@test.edu"
    assert data["role"] == "student"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, seeded_university):
    payload = {
        "full_name": "Duplicate",
        "email": "dup@test.edu",
        "password": "Test@1234",
        "university_id": seeded_university["id"],
    }
    client.post("/auth/register", json=payload)
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 409


def test_login_success(client, seeded_university):
    client.post("/auth/register", json={
        "full_name": "Login Test",
        "email": "logintest@test.edu",
        "password": "Test@1234",
        "university_id": seeded_university["id"],
    })
    r = client.post("/auth/login", json={
        "email": "logintest@test.edu",
        "password": "Test@1234",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, seeded_university):
    client.post("/auth/register", json={
        "full_name": "Wrong Pass",
        "email": "wrongpass@test.edu",
        "password": "Right@1234",
        "university_id": seeded_university["id"],
    })
    r = client.post("/auth/login", json={
        "email": "wrongpass@test.edu",
        "password": "Wrong@1234",
    })
    assert r.status_code == 401


def test_get_profile_authenticated(client, student_token):
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 200
    assert r.json()["department"] == "CSE"


def test_get_profile_unauthenticated(client):
    r = client.get("/auth/me")
    # No token → FastAPI HTTPBearer returns 401 or 403 depending on version
    assert r.status_code in (401, 403)
