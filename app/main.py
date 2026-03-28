"""
FastAPI application entry point.
All routers registered here.
CORS configured for development (restrict origins in production).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, documents, query, universities

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-university academic intelligence platform",
    version="1.0.0",
    docs_url="/docs",    # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)

# CORS — allow all origins in dev, restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(universities.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
