# API Reference — Multi-Modal Attendance System

Base URL: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (Swagger UI)

All protected endpoints require:
```
Authorization: Bearer <jwt_token>
```

The token is obtained from `POST /api/auth/login`.

---

## Authentication

### POST `/api/auth/login`
Login as admin.

**Request body (form data):**
```
username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@attendance.local"
  }
}
```

### GET `/api/auth/me`
Get current admin info. Requires auth.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@attendance.local",
  "is_active": true
}
```

### POST `/api/auth/logout`
Logout (client discards token).

---

## Students

### GET `/api/students/`
List all students with optional filters.

**Query params:**
| Param | Type | Description |
|---|---|---|
| `search` | string | Search by name or student_id |
| `department` | string | Filter by department |
| `year` | int | Filter by year |
| `page` | int | Page number (default 1) |
| `per_page` | int | Items per page (default 20) |

**Response:**
```json
{
  "students": [...],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### POST `/api/students/`
Create a new student. Requires auth.

**Request body:**
```json
{
  "student_id": "CSE2024010",
  "name": "John Doe",
  "department": "CSE",
  "year": 1,
  "section": "A",
  "email": "john@college.edu",
  "phone": "9876543210"
}
```

### GET `/api/students/{student_id}`
Get a single student by their internal DB `id`.

**Response includes:**
```json
{
  "id": 1,
  "student_id": "CSE2024001",
  "name": "Arun Kumar",
  ...
  "enrollment_status": {
    "face": true,
    "palm": false,
    "fingerprint": true
  }
}
```

### PUT `/api/students/{student_id}`
Update student details. Requires auth.

### DELETE `/api/students/{student_id}`
Soft-delete (deactivate) a student. Requires auth.

### GET `/api/students/{student_id}/enrollment-status`
Check which biometric modalities are enrolled for a student.

**Response:**
```json
{
  "student_id": 1,
  "face": true,
  "palm": false,
  "fingerprint": true
}
```

---

## Enrollment

### POST `/api/enrollment/face/{student_id}`
Enroll or re-enroll face biometric. Requires auth.

**Request body:**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Face enrolled successfully",
  "quality_score": 0.92,
  "student_id": 1
}
```

### POST `/api/enrollment/palm/{student_id}`
Enroll palm/hand biometric. Requires auth.

**Request body:**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

### POST `/api/enrollment/fingerprint/{student_id}`
Enroll fingerprint (simulated). Requires auth.

**Request body:**
```json
{}
```
(No image required for simulated mode. In real mode, pass scanner data.)

### DELETE `/api/enrollment/face/{student_id}`
Remove face template for student. Requires auth.

### DELETE `/api/enrollment/palm/{student_id}`
Remove palm template for student. Requires auth.

### DELETE `/api/enrollment/fingerprint/{student_id}`
Remove fingerprint template for student. Requires auth.

---

## Attendance

### POST `/api/attendance/verify/face`
Verify identity using face recognition. Requires auth.

**Request body:**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response (match found):**
```json
{
  "match": true,
  "student_id": 1,
  "student_name": "Arun Kumar",
  "student_code": "CSE2024001",
  "score": 0.87,
  "message": "Face verified successfully",
  "already_marked_today": false
}
```

**Response (no match):**
```json
{
  "match": false,
  "score": 0.31,
  "message": "Face not recognized. Please try again."
}
```

### POST `/api/attendance/verify/palm`
Verify identity using palm recognition. Requires auth.

Same request/response structure as face verification.

### POST `/api/attendance/verify/fingerprint`
Verify identity using fingerprint (simulated). Requires auth.

**Request body:**
```json
{
  "student_id": 1
}
```
(In simulated mode, student_id is required. In real mode, the scanner identifies the student.)

### POST `/api/attendance/verify/multimodal`
Fused multi-modal verification + attendance recording. Requires auth.

**Request body:**
```json
{
  "face_image": "data:image/jpeg;base64,...",
  "palm_image": "data:image/jpeg;base64,...",
  "use_fingerprint": false
}
```
Any combination is valid (at least one modality required; two recommended).

**Response:**
```json
{
  "match": true,
  "student_id": 1,
  "student_name": "Arun Kumar",
  "student_code": "CSE2024001",
  "individual_scores": {
    "face": 0.89,
    "palm": 0.82,
    "fingerprint": null
  },
  "fusion_score": 0.87,
  "modalities_used": ["face", "palm"],
  "decision": "verified",
  "attendance_recorded": true,
  "attendance_status": "present",
  "message": "Attendance marked successfully"
}
```

### GET `/api/attendance/`
List attendance records with filters. Requires auth.

**Query params:**
| Param | Type | Description |
|---|---|---|
| `date_from` | date | Start date (YYYY-MM-DD) |
| `date_to` | date | End date (YYYY-MM-DD) |
| `student_id` | int | Filter by student DB ID |
| `department` | string | Filter by department |
| `status` | string | present/late/absent |
| `page` | int | Page number |
| `per_page` | int | Items per page |

### GET `/api/attendance/today`
Get today's attendance records. Requires auth.

### GET `/api/attendance/stats`
Get summary statistics. Requires auth.

**Response:**
```json
{
  "total_students": 50,
  "present_today": 42,
  "absent_today": 8,
  "late_today": 5,
  "attendance_rate": 84.0,
  "last_7_days": [
    {"date": "2024-01-01", "present": 40, "absent": 10, "late": 3},
    ...
  ]
}
```

---

## Reports

### GET `/api/reports/daily`
Daily attendance report. Requires auth.

**Query param:** `date` (YYYY-MM-DD, default today)

### GET `/api/reports/weekly`
Weekly attendance report. Requires auth.

**Query param:** `week_start` (YYYY-MM-DD, Monday of the week)

### GET `/api/reports/monthly`
Monthly attendance report. Requires auth.

**Query params:** `year`, `month`

### GET `/api/reports/student/{student_id}`
Full attendance history for one student. Requires auth.

### GET `/api/reports/export/csv`
Download CSV file. Requires auth.

**Query params:**
- `date_from` (YYYY-MM-DD)
- `date_to` (YYYY-MM-DD)
- `department` (optional)

**Response:** `Content-Type: text/csv` file download

### GET `/api/reports/export/pdf`
Download PDF file. Requires auth.

Same query params as CSV.

**Response:** `Content-Type: application/pdf` file download

### GET `/api/reports/summary`
Overall system statistics. Requires auth.

**Response:**
```json
{
  "total_students": 50,
  "enrolled": {
    "face": 48,
    "palm": 30,
    "fingerprint": 20
  },
  "overall_attendance_rate": 82.5,
  "this_month_records": 1240
}
```

---

## Settings

### GET `/api/settings/`
Get all system settings. Requires auth.

**Response:**
```json
[
  {
    "id": 1,
    "key": "face_threshold",
    "value": "0.50",
    "description": "Minimum face similarity score (0.0-1.0)"
  },
  ...
]
```

### PUT `/api/settings/`
Update one or more settings. Requires auth.

**Request body:**
```json
[
  { "key": "face_threshold", "value": "0.55" },
  { "key": "fusion_threshold", "value": "0.65" }
]
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

| Status Code | Meaning |
|---|---|
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (e.g., duplicate student ID) |
| 422 | Unprocessable entity (invalid request body) |
| 500 | Internal server error |

---

## Quick Test with curl

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -F "username=admin" -F "password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# List students
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/students/

# Get today's stats
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/attendance/stats

# Get today's attendance
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/attendance/today
```
