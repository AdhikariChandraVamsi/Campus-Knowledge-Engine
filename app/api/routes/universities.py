"""University management — seed data and listing."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.university import University

router = APIRouter(prefix="/universities", tags=["Universities"])


class UniversityCreate(BaseModel):
    name: str
    slug: str
    city: str = ""


class UniversityResponse(BaseModel):
    id: str
    name: str
    slug: str
    city: str

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[UniversityResponse])
def list_universities(db: Session = Depends(get_db)):
    """List all active universities (for registration dropdown)."""
    return db.query(University).filter(University.is_active == True).all()


@router.post("/", response_model=UniversityResponse, status_code=201)
def create_university(data: UniversityCreate, db: Session = Depends(get_db)):
    """Create a university (use for seeding — secure this in production)."""
    import uuid
    uni = University(
        id=str(uuid.uuid4()),
        name=data.name,
        slug=data.slug,
        city=data.city,
    )
    db.add(uni)
    db.commit()
    db.refresh(uni)
    return uni
