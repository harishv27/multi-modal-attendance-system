import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.connection import engine, Base, SessionLocal
from database.models import Admin, SystemSetting
from utils.security import hash_password

from routers import auth, students, enrollment, attendance, reports, settings

app = FastAPI(title="Multi-Modal Attendance System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(enrollment.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed Admin
        admin = db.query(Admin).filter(Admin.username == "admin").first()
        if not admin:
            new_admin = Admin(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123")
            )
            db.add(new_admin)
            
        # Seed Settings
        default_settings = [
            ("FACE_THRESHOLD", "0.50", "Face threshold"),
            ("PALM_THRESHOLD", "0.70", "Palm threshold"),
            ("FINGERPRINT_THRESHOLD", "0.75", "Fingerprint threshold"),
            ("FUSION_THRESHOLD", "0.60", "Fusion threshold"),
            ("FACE_WEIGHT", "0.45", "Face weight"),
            ("FINGERPRINT_WEIGHT", "0.35", "Fingerprint weight"),
            ("PALM_WEIGHT", "0.20", "Palm weight")
        ]
        
        for k, v, d in default_settings:
            s = db.query(SystemSetting).filter(SystemSetting.key == k).first()
            if not s:
                db.add(SystemSetting(key=k, value=v, description=d))
                
        db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Multi-Modal Attendance System API", "docs": "/docs"}
