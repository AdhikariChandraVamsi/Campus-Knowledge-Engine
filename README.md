# Campus Knowledge Engine

Multi-university academic intelligence platform.

## Quick Start (Local Dev)
```bash
# 1. Activate venv
source venv/bin/activate

# 2. Start PostgreSQL (via Docker)
docker-compose up db -d

# 3. Run migrations
alembic upgrade head

# 4. Start API
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Full Stack (Docker)
```bash
docker-compose up --build
```

## Project Structure
```
app/
├── api/routes/       # Thin route handlers
├── core/             # Config, security, dependencies
├── db/               # Session and base
├── models/           # SQLAlchemy ORM models (DB tables)
├── pipeline/         # PDF → chunks → embeddings
├── schemas/          # Pydantic request/response shapes
└── services/         # Business logic layer
```

## Key Design Decisions
- Routes stay thin — all logic in services/
- university_id is the isolation boundary — every DB and ChromaDB query filters by it
- Similarity threshold prevents hallucination — below threshold = "no data" response
- Background tasks — upload returns instantly, pipeline runs async
- Alembic migrations — never drop-recreate DB, always migrate
