-- =============================================================================
-- MULTI-MODAL ATTENDANCE SYSTEM — Database Schema
-- =============================================================================
-- Database: MySQL 8.0+
-- Run this file to create the database from scratch:
--   mysql -u root -p < database/schema.sql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS attendance_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE attendance_db;

-- =============================================================================
-- TABLE: admins
-- =============================================================================
CREATE TABLE IF NOT EXISTS admins (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_admins_username (username)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: students
-- =============================================================================
CREATE TABLE IF NOT EXISTS students (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    student_id    VARCHAR(20)  NOT NULL UNIQUE,
    name          VARCHAR(100) NOT NULL,
    department    VARCHAR(50)  NOT NULL,
    year          TINYINT      NOT NULL,
    section       VARCHAR(5)   NOT NULL,
    email         VARCHAR(100),
    phone         VARCHAR(15),
    photo_path    VARCHAR(255),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_students_student_id (student_id),
    INDEX idx_students_department (department),
    INDEX idx_students_is_active (is_active)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: face_templates
-- =============================================================================
CREATE TABLE IF NOT EXISTS face_templates (
    id            INT         AUTO_INCREMENT PRIMARY KEY,
    student_id    INT         NOT NULL,
    embedding     MEDIUMTEXT  NOT NULL,
    quality_score FLOAT       NOT NULL DEFAULT 0.0,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY uq_face_student (student_id)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: palm_templates
-- =============================================================================
CREATE TABLE IF NOT EXISTS palm_templates (
    id            INT         AUTO_INCREMENT PRIMARY KEY,
    student_id    INT         NOT NULL,
    embedding     MEDIUMTEXT  NOT NULL,
    quality_score FLOAT       NOT NULL DEFAULT 0.0,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY uq_palm_student (student_id)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: fingerprint_templates
-- =============================================================================
CREATE TABLE IF NOT EXISTS fingerprint_templates (
    id            INT         AUTO_INCREMENT PRIMARY KEY,
    student_id    INT         NOT NULL,
    template      MEDIUMTEXT  NOT NULL,
    quality_score FLOAT       NOT NULL DEFAULT 0.0,
    created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY uq_fingerprint_student (student_id)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: attendance
-- =============================================================================
CREATE TABLE IF NOT EXISTS attendance (
    id                  INT         AUTO_INCREMENT PRIMARY KEY,
    student_id          INT         NOT NULL,
    date                DATE        NOT NULL,
    time_in             TIME        NOT NULL,
    face_score          FLOAT,
    palm_score          FLOAT,
    fingerprint_score   FLOAT,
    fusion_score        FLOAT,
    verification_method VARCHAR(20) NOT NULL DEFAULT 'face',
    status              VARCHAR(10) NOT NULL DEFAULT 'present',
    notes               TEXT,
    created_at          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_attendance_student_id (student_id),
    INDEX idx_attendance_date (date),
    INDEX idx_attendance_status (status),
    UNIQUE KEY uq_attendance_student_date (student_id, date)
) ENGINE=InnoDB;

-- =============================================================================
-- TABLE: system_settings
-- =============================================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    `key`       VARCHAR(100) NOT NULL UNIQUE,
    value       TEXT         NOT NULL,
    description TEXT,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =============================================================================
-- DEFAULT DATA
-- Admin: username=admin, password=admin123
-- =============================================================================
INSERT IGNORE INTO admins (username, email, password_hash)
VALUES (
    'admin',
    'admin@attendance.local',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'
);

INSERT IGNORE INTO system_settings (`key`, value, description) VALUES
('face_threshold',             '0.50', 'Minimum face similarity score (0.0-1.0)'),
('palm_threshold',             '0.70', 'Minimum palm similarity score (0.0-1.0)'),
('fingerprint_threshold',      '0.75', 'Minimum fingerprint match score (0.0-1.0)'),
('fusion_threshold',           '0.60', 'Minimum fusion score for verification (0.0-1.0)'),
('face_weight',                '0.45', 'Face weight in fusion algorithm'),
('fingerprint_weight',         '0.35', 'Fingerprint weight in fusion algorithm'),
('palm_weight',                '0.20', 'Palm weight in fusion algorithm'),
('late_cutoff_hour',           '9',    'Hour (24h) after which attendance is Late'),
('late_cutoff_minute',         '15',   'Minute after which attendance is Late'),
('system_name',                'Multi-Modal Attendance System', 'System display name'),
('institution_name',           'Your College Name', 'Institution name for reports'),
('allow_duplicate_prevention', 'true', 'Prevent marking attendance twice per day'),
('fingerprint_mode',           'simulated', 'Set to real when real SDK is connected');

SELECT 'Database schema created successfully.' AS status;
