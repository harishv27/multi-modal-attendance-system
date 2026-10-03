from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    section = Column(String(10), nullable=False)
    email = Column(String(100), unique=True, nullable=True)   # optional
    phone = Column(String(20), nullable=True)
    photo_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    face_templates         = relationship("FaceTemplate",         back_populates="student", cascade="all, delete-orphan")
    palm_templates         = relationship("PalmTemplate",         back_populates="student", cascade="all, delete-orphan")
    fingerprint_templates  = relationship("FingerprintTemplate",  back_populates="student", cascade="all, delete-orphan")
    attendances            = relationship("Attendance",           back_populates="student", cascade="all, delete-orphan")

class FaceTemplate(Base):
    __tablename__ = "face_templates"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    embedding = Column(Text, nullable=False)
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    student = relationship("Student", back_populates="face_templates")

class PalmTemplate(Base):
    __tablename__ = "palm_templates"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    hand_side = Column(String(10), nullable=False, default="right")  # "left" or "right"
    embedding = Column(Text, nullable=False)
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    student = relationship("Student", back_populates="palm_templates")


class FingerprintTemplate(Base):
    __tablename__ = "fingerprint_templates"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    template = Column(Text, nullable=False)
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    student = relationship("Student", back_populates="fingerprint_templates")

class Attendance(Base):
    __tablename__ = "attendance"           # matches schema.sql
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    time_in = Column(Time, nullable=False)
    face_score = Column(Float, nullable=True)
    palm_score = Column(Float, nullable=True)
    fingerprint_score = Column(Float, nullable=True)
    fusion_score = Column(Float, nullable=True)
    verification_method = Column(String(50), nullable=False, default="face")
    status = Column(String(20), nullable=False, default="present")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    student = relationship("Student", back_populates="attendances")

class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

