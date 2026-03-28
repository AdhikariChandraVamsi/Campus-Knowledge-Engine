"""
Seed script — creates university + admin + sample student.
Run once after migrations: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.university import University
from app.models.user import User, UserRole
from app.core.security import hash_password
import uuid

db = SessionLocal()

try:
    # Check if already seeded
    existing = db.query(University).filter(University.slug == "amrita_cb").first()
    if existing:
        print(f"✅ Already seeded. University ID: {existing.id}")
        uni_id = existing.id
    else:
        # Create university
        uni = University(
            id=str(uuid.uuid4()),
            name="Amrita School of Engineering, Coimbatore",
            slug="amrita_cb",
            city="Coimbatore",
        )
        db.add(uni)
        db.commit()
        db.refresh(uni)
        uni_id = uni.id
        print(f"✅ University created: {uni.name}")
        print(f"   ID: {uni_id}")

    # Admin account
    admin_email = "admin@amrita.edu"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        admin = User(
            id=str(uuid.uuid4()),
            university_id=uni_id,
            email=admin_email,
            hashed_password=hash_password("Admin@1234"),
            full_name="CKE Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        print(f"✅ Admin created: {admin_email} / Admin@1234")
    else:
        print(f"✅ Admin already exists: {admin_email}")

    # Student account
    student_email = "student@amrita.edu"
    existing_student = db.query(User).filter(User.email == student_email).first()
    if not existing_student:
        student = User(
            id=str(uuid.uuid4()),
            university_id=uni_id,
            email=student_email,
            hashed_password=hash_password("Student@1234"),
            full_name="Test Student",
            role=UserRole.STUDENT,
            department="CSE",
            semester="5",
            section="F",
            regulation="2023",
            is_active=True,
            is_verified=True,
        )
        db.add(student)
        db.commit()
        print(f"✅ Student created: {student_email} / Student@1234")
        print(f"   Profile: CSE | Sem 5 | Section F | Reg 2023")
    else:
        print(f"✅ Student already exists: {student_email}")

    print("\n🎯 Seed complete. Save this University ID:")
    print(f"   UNIVERSITY_ID={uni_id}")

except Exception as e:
    print(f"❌ Seed failed: {e}")
    db.rollback()
finally:
    db.close()
