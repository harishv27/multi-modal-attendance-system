from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from database.connection import get_db
from database.models import Student, FaceTemplate, PalmTemplate, FingerprintTemplate
from services.face_service import encode_face, check_duplicate_face
from services.palm_service import extract_palm_features, check_duplicate_palm
from routers.auth import get_current_admin

router = APIRouter(prefix="/enrollment", tags=["enrollment"], dependencies=[Depends(get_current_admin)])


class ImagePayload(BaseModel):
    image_base64: str
    hand_side: Optional[str] = None  # "left" or "right" — optional hint, auto-detected


class FingerprintPayload(BaseModel):
    credential_id: str


# ─── Face ──────────────────────────────────────────────────────────────────

@router.post("/face/{student_id}")
def enroll_face(student_id: int, payload: ImagePayload, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        result = encode_face(payload.image_base64.encode("utf-8"))

        # ── Duplicate detection ──────────────────────────────────────────
        existing_templates = (
            db.query(FaceTemplate)
            .filter(FaceTemplate.student_id != student_id)   # exclude THIS student
            .all()
        )
        if existing_templates:
            template_list = [
                {"student_id": t.student_id, "embedding": json.loads(t.embedding)}
                for t in existing_templates
            ]
            dup = check_duplicate_face(result["embedding"], template_list, duplicate_threshold=0.85)
            if dup["is_duplicate"]:
                existing_student = db.query(Student).filter(
                    Student.id == dup["existing_student_id"]
                ).first()
                name = existing_student.name if existing_student else f"ID {dup['existing_student_id']}"
                raise HTTPException(
                    status_code=409,
                    detail=f"This face is already registered to '{name}' "
                           f"(similarity {dup['score']*100:.1f}%). "
                           f"Duplicate biometrics are not allowed."
                )

        # ── Overwrite this student's existing face template ──────────────
        db.query(FaceTemplate).filter(FaceTemplate.student_id == student_id).delete()
        db.add(FaceTemplate(
            student_id=student_id,
            embedding=json.dumps(result["embedding"]),
            quality_score=result["quality_score"],
        ))
        db.commit()
        return {"message": "Face enrolled successfully", "quality_score": result["quality_score"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Palm (auto-detects Left / Right) ───────────────────────────────────────

@router.post("/palm/{student_id}")
def enroll_palm(student_id: int, payload: ImagePayload, db: Session = Depends(get_db)):
    """
    Enroll a palm print.  The backend auto-detects which hand is shown.
    The optional `hand_side` field in the payload is used only as a label hint
    if MediaPipe cannot determine handedness — it is never enforced strictly.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        result = extract_palm_features(payload.image_base64.encode("utf-8"))

        # Use auto-detected side; fall back to hint if detection uncertain
        hand_side = result.get("hand_side") or payload.hand_side or "right"

        # ── Duplicate detection (all palms from other students) ──────────
        existing_templates = (
            db.query(PalmTemplate)
            .filter(PalmTemplate.student_id != student_id)
            .all()
        )
        if existing_templates:
            template_list = [
                {"student_id": t.student_id, "embedding": json.loads(t.embedding)}
                for t in existing_templates
            ]
            dup = check_duplicate_palm(result["embedding"], template_list, duplicate_threshold=0.95)
            if dup["is_duplicate"]:
                existing_student = db.query(Student).filter(
                    Student.id == dup["existing_student_id"]
                ).first()
                name = existing_student.name if existing_student else f"ID {dup['existing_student_id']}"
                raise HTTPException(
                    status_code=409,
                    detail=f"This palm is already registered to '{name}' "
                           f"(similarity {dup['score']*100:.1f}%). "
                           f"Duplicate biometrics are not allowed."
                )

        # ── Overwrite template for this hand side only ───────────────────
        db.query(PalmTemplate).filter(
            PalmTemplate.student_id == student_id,
            PalmTemplate.hand_side == hand_side,
        ).delete()
        db.add(PalmTemplate(
            student_id=student_id,
            hand_side=hand_side,
            embedding=json.dumps(result["embedding"]),
            quality_score=result["quality_score"],
        ))
        db.commit()
        return {
            "message": f"{hand_side.capitalize()} palm enrolled successfully",
            "hand_side": hand_side,
            "quality_score": result["quality_score"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Fingerprint (WebAuthn / Touch ID) ─────────────────────────────────────

@router.post("/fingerprint/{student_id}")
def enroll_fingerprint(
    student_id: int,
    payload: FingerprintPayload,
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        db.query(FingerprintTemplate).filter(
            FingerprintTemplate.student_id == student_id
        ).delete()
        db.add(FingerprintTemplate(
            student_id=student_id,
            template=payload.credential_id,
            quality_score=1.0,
        ))
        db.commit()
        return {"message": "Fingerprint (Touch ID) enrolled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Delete endpoints ───────────────────────────────────────────────────────

@router.delete("/face/{student_id}")
def delete_face(student_id: int, db: Session = Depends(get_db)):
    db.query(FaceTemplate).filter(FaceTemplate.student_id == student_id).delete()
    db.commit()
    return {"message": "Face template removed"}


@router.delete("/palm/{student_id}")
def delete_palm(
    student_id: int,
    hand_side: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PalmTemplate).filter(PalmTemplate.student_id == student_id)
    if hand_side:
        q = q.filter(PalmTemplate.hand_side == hand_side)
    q.delete()
    db.commit()
    return {"message": "Palm template(s) removed"}


@router.delete("/fingerprint/{student_id}")
def delete_fingerprint(student_id: int, db: Session = Depends(get_db)):
    db.query(FingerprintTemplate).filter(
        FingerprintTemplate.student_id == student_id
    ).delete()
    db.commit()
    return {"message": "Fingerprint template removed"}
