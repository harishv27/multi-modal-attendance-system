from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
import json
from datetime import datetime, date

from database.connection import get_db
from database.models import Student, FaceTemplate, PalmTemplate, FingerprintTemplate, Attendance, SystemSetting
from services.face_service import encode_face, get_best_match as get_best_face
from services.palm_service import extract_palm_features, get_best_match as get_best_palm
from services.fingerprint_service import verify_fingerprint, get_best_match as get_best_fingerprint
from services.fusion_service import fuse_scores
from routers.auth import get_current_admin

router = APIRouter(prefix="/attendance", tags=["attendance"])

class ImagePayload(BaseModel):
    image_base64: str

class MultiModalPayload(BaseModel):
    face_image: Optional[str] = None
    palm_image: Optional[str] = None
    fingerprint_credential_id: Optional[str] = None

def get_settings(db: Session):
    settings = db.query(SystemSetting).all()
    return {s.key: float(s.value) if s.value.replace('.','',1).isdigit() else s.value for s in settings}

@router.post("/verify/face")
def verify_face(payload: ImagePayload, db: Session = Depends(get_db)):
    settings = get_settings(db)
    threshold = settings.get('FACE_THRESHOLD', 0.5)
    
    try:
        live_result = encode_face(payload.image_base64.encode('utf-8'))
        all_templates = db.query(FaceTemplate).all()
        template_list = [{"student_id": t.student_id, "embedding": json.loads(t.embedding)} for t in all_templates]
        
        match = get_best_face(live_result['embedding'], template_list, threshold)
        
        if match['match']:
            student = db.query(Student).filter(Student.id == match['student_id']).first()
            return {
                "student_id": student.id,
                "student_name": student.name,
                "score": match['score'],
                "match": True,
                "message": "Face verified successfully"
            }
        return {"match": False, "message": "No match found"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/palm")
def verify_palm(payload: ImagePayload, db: Session = Depends(get_db)):
    settings = get_settings(db)
    threshold = settings.get('PALM_THRESHOLD', 0.7)
    
    try:
        live_result = extract_palm_features(payload.image_base64.encode('utf-8'))
        all_templates = db.query(PalmTemplate).all()
        template_list = [{"student_id": t.student_id, "embedding": json.loads(t.embedding)} for t in all_templates]
        
        match = get_best_palm(live_result['embedding'], template_list, threshold)
        
        if match['match']:
            student = db.query(Student).filter(Student.id == match['student_id']).first()
            return {
                "student_id": student.id,
                "student_name": student.name,
                "score": match['score'],
                "match": True,
                "message": "Palm verified successfully"
            }
        return {"match": False, "message": "No match found"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/fingerprint")
def verify_finger_print(db: Session = Depends(get_db)):
    # Legacy simulated verify
    return {"match": False, "message": "Endpoint retired. Use multimodal."}

@router.post("/verify/multimodal")
def verify_multimodal(payload: MultiModalPayload, db: Session = Depends(get_db)):
    settings = get_settings(db)
    
    face_score = None
    palm_score = None
    fingerprint_score = None
    student_matches = {}
    
    try:
        if payload.face_image:
            live_result = encode_face(payload.face_image.encode('utf-8'))
            all_templates = db.query(FaceTemplate).all()
            template_list = [{"student_id": t.student_id, "embedding": json.loads(t.embedding)} for t in all_templates]
            match = get_best_face(live_result['embedding'], template_list, settings.get('FACE_THRESHOLD', 0.5))
            if match['match']:
                face_score = match['score']
                student_matches[match['student_id']] = student_matches.get(match['student_id'], 0) + 1

        if payload.palm_image:
            live_result = extract_palm_features(payload.palm_image.encode('utf-8'))
            all_templates = db.query(PalmTemplate).all()
            template_list = [{"student_id": t.student_id, "embedding": json.loads(t.embedding)} for t in all_templates]
            match = get_best_palm(live_result['embedding'], template_list, settings.get('PALM_THRESHOLD', 0.7))
            if match['match']:
                palm_score = match['score']
                student_matches[match['student_id']] = student_matches.get(match['student_id'], 0) + 1
                
        if payload.fingerprint_credential_id:
            template = db.query(FingerprintTemplate).filter(FingerprintTemplate.template == payload.fingerprint_credential_id).first()
            if template:
                fingerprint_score = 1.0 # 100% match if credential exists
                student_matches[template.student_id] = student_matches.get(template.student_id, 0) + 1

        if not student_matches:
            return {"match": False, "message": "No matches found across provided modalities"}
            
        # Get the most agreed upon student
        best_student_id = max(student_matches, key=student_matches.get)
        student = db.query(Student).filter(Student.id == best_student_id).first()
        
        # Fuse scores
        weights = {
            'FACE': settings.get('FACE_WEIGHT', 0.45),
            'FINGERPRINT': settings.get('FINGERPRINT_WEIGHT', 0.35),
            'PALM': settings.get('PALM_WEIGHT', 0.20)
        }
        
        fusion_result = fuse_scores(face_score, fingerprint_score, palm_score, weights, settings)
        
        if fusion_result['decision'] == 'verified':
            # Record attendance
            new_attendance = Attendance(
                student_id=best_student_id,
                date=datetime.now().date(),
                time_in=datetime.now().time(),
                face_score=face_score,
                palm_score=palm_score,
                fingerprint_score=fingerprint_score,
                fusion_score=fusion_result['fusion_score'],
                verification_method="multimodal",
                status="present"
            )
            db.add(new_attendance)
            db.commit()
            
        return {
            "student_id": student.id,
            "student_name": student.name,
            "fusion_result": fusion_result,
            "match": fusion_result['decision'] == 'verified'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_attendance(
    date_from:  Optional[date] = None,
    date_to:    Optional[date] = None,
    student_id: Optional[int]  = None,
    status:     Optional[str]  = None,
    department: Optional[str]  = None,
    db:         Session        = Depends(get_db),
    _:          None           = Depends(get_current_admin),
):
    query = db.query(Attendance).join(Student)
    if date_from:   query = query.filter(Attendance.date >= date_from)
    if date_to:     query = query.filter(Attendance.date <= date_to)
    if student_id:  query = query.filter(Attendance.student_id == student_id)
    if status:      query = query.filter(Attendance.status == status)
    if department:  query = query.filter(Student.department == department)

    records = query.order_by(Attendance.date.desc(), Attendance.time_in.desc()).all()
    return [
        {
            "id":                  r.id,
            "date":                r.date.isoformat()    if r.date    else None,
            "time_in":             str(r.time_in)        if r.time_in else None,
            "face_score":          r.face_score,
            "palm_score":          r.palm_score,
            "fingerprint_score":   r.fingerprint_score,
            "fusion_score":        r.fusion_score,
            "verification_method": r.verification_method,
            "status":              r.status,
            "student": {
                "name":       r.student.name,
                "student_id": r.student.student_id,
                "department": r.student.department,
            },
        }
        for r in records
    ]


@router.get("/today")
def get_today_attendance(
    db: Session = Depends(get_db),
    _:  None    = Depends(get_current_admin),
):
    today = datetime.now().date()
    records = db.query(Attendance).filter(Attendance.date == today).all()
    return [
        {
            "id":      r.id,
            "time_in": str(r.time_in) if r.time_in else None,
            "status":  r.status,
            "student": {
                "name":       r.student.name,
                "student_id": r.student.student_id,
            },
        }
        for r in records
    ]


@router.get("/stats")
def get_attendance_stats(
    db: Session = Depends(get_db),
    _:  None    = Depends(get_current_admin),
):
    today          = datetime.now().date()
    total_students = db.query(Student).filter(Student.is_active == True).count()
    present_today  = db.query(Attendance).filter(Attendance.date == today, Attendance.status == "present").count()
    late_today     = db.query(Attendance).filter(Attendance.date == today, Attendance.status == "late").count()
    absent_today   = max(0, total_students - (present_today + late_today))

    return {
        "total_students": total_students,
        "present_today":  present_today,
        "late_today":     late_today,
        "absent_today":   absent_today,
        "last_7_days":    [],   # placeholder — populated by reports endpoint
    }

