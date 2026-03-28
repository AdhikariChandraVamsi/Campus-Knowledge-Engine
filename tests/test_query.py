"""Query endpoint tests."""


def test_query_requires_auth(client):
    # No token → FastAPI HTTPBearer returns 401 or 403 depending on version
    r = client.post("/query/", json={"question": "What is my timetable?"})
    assert r.status_code in (401, 403)


def test_query_invalid_token(client):
    # Bad token — always 401
    r = client.post(
        "/query/",
        headers={"Authorization": "Bearer this-is-not-a-valid-token"},
        json={"question": "What is my timetable?"},
    )
    assert r.status_code == 401


def test_query_returns_structure(client, student_token):
    """Query with no indexed documents — should return was_answered=False."""
    r = client.post(
        "/query/",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"question": "What subjects do I have on Monday?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "was_answered" in data
    assert "chunks_used" in data


def test_query_clarification_timetable_no_section(client, seeded_university):
    """Student with no section asks timetable question — should get clarification back."""
    client.post("/auth/register", json={
        "full_name": "No Section Student",
        "email": "nosection@test.edu",
        "password": "Test@1234",
        "university_id": seeded_university["id"],
        "role": "student",
        "department": "CSE",
        "semester": "5",
    })
    r = client.post("/auth/login", json={
        "email": "nosection@test.edu",
        "password": "Test@1234",
    })
    token = r.json()["access_token"]

    r = client.post(
        "/query/",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is my timetable on Monday?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["clarification_needed"] is not None
