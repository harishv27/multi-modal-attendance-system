# 🎓 Multi-Modal Attendance System

A biometric attendance system that uses **Face Recognition + Palm Print (Left & Right) + Fingerprint (Touch ID)** for secure, multi-factor student identification.

---

## 🖥️ Tech Stack

| Layer        | Technology                                  |
|-------------|---------------------------------------------|
| Frontend     | React 18, Vite, Tailwind CSS                |
| Backend      | FastAPI (Python 3.11), Uvicorn              |
| Database     | MySQL 8.x + SQLAlchemy ORM                 |
| Face AI      | FaceNet (facenet-pytorch, VGGFace2 model)   |
| Palm AI      | MediaPipe Hands (21 landmark detection)     |
| Fingerprint  | WebAuthn (Touch ID / Windows Hello)         |

---

## 📋 Prerequisites

- macOS (or Windows/Linux) with Python 3.11
- MySQL 8.x running locally
- Node.js 18+ and npm
- (Optional) Mac with Touch ID for fingerprint enrollment

---

## ⚡ Quick Setup

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd "MULTI-MODAL ATTENDANCE SYSTEM"
```

### 2. Create MySQL Database

```sql
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'attendance_user'@'localhost' IDENTIFIED BY 'attend@2024';
GRANT ALL PRIVILEGES ON attendance_db.* TO 'attendance_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Backend Setup

```bash
# Create virtual environment (Python 3.11 recommended)
python3.11 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your MySQL credentials
```

**`.env` file:**
```
DATABASE_URL=mysql+pymysql://attendance_user:attend@2024@localhost:3306/attendance_db
SECRET_KEY=your-super-secret-key-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
FACE_THRESHOLD=0.50
PALM_THRESHOLD=0.70
FINGERPRINT_THRESHOLD=0.75
FUSION_THRESHOLD=0.60
FACE_WEIGHT=0.45
FINGERPRINT_WEIGHT=0.35
PALM_WEIGHT=0.20
```

```bash
# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend API runs at: `http://localhost:8000`  
API Docs (Swagger): `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 5. Default Admin Login

```
Username: admin
Password: admin123
```

---

## 🚀 How to Use

### Register a New Student

1. Go to **Students → Add Student**
2. Fill in: Student ID, Name, Department, Year, Section
3. **Step 2 — Face Enrollment**: Look at the camera. Wait for the green box to appear around your face, then click **Capture**
4. **Step 3 — Right Palm**: Show your right palm flat to the camera. Wait for the blue box, then click **Capture**
5. **Step 4 — Left Palm**: Show your left palm flat to the camera. Wait for the blue box, then click **Capture**
6. **Step 5 — Fingerprint**: Click **Scan Fingerprint** to use Touch ID (Mac) or Windows Hello. If your system has no fingerprint reader, this step shows "Not Available" — click Skip.

### Mark Attendance

1. Go to **Mark Attendance**
2. **Step 1**: Look at the camera for face recognition
3. **Step 2**: Show palm for palm verification
4. **Step 3**: Use Touch ID for fingerprint verification
5. The system runs multi-modal fusion and marks attendance if verified

---

## 🧠 How the AI Works

### Face Recognition
- Uses **FaceNet** (`facenet-pytorch`) with VGGFace2 pre-trained weights
- MTCNN detects the face bounding box
- InceptionResnetV1 generates a **512-dimensional embedding**
- Match comparison uses **Euclidean distance** (threshold: 0.50)

### Palm Recognition
- Uses **MediaPipe Hands** to detect 21 3D hand landmarks
- Generates a **63-dimensional feature vector** (21 landmarks × x,y,z)
- Automatically detects **left vs. right** hand (accounts for camera mirror)
- Match comparison uses **cosine similarity** (threshold: 0.70)

### Fingerprint (Touch ID)
- Uses **WebAuthn Platform Authenticator** (`navigator.credentials.create/get`)
- Forces device biometrics only (`authenticatorAttachment: "platform"`)
- Does NOT use a password manager — uses Touch ID directly
- If no fingerprint reader is detected, displays a clear message

### Score Fusion
- Combines Face (45%) + Fingerprint (35%) + Palm (20%) scores
- Fusion score ≥ 0.60 → **VERIFIED**
- Attendance is recorded in the database only upon verification

---

## 🔑 Biometric Detection — Live Camera Tips

| Biometric   | Tips for Best Detection |
|------------|-------------------------|
| **Face**   | Look directly at camera, ensure good lighting, neutral expression |
| **Palm**   | Hold hand flat and open, palm facing camera, arm extended |
| **Fingerprint** | Place finger firmly on Touch ID sensor when browser prompts |

---

## 📂 Project Structure

```
MULTI-MODAL ATTENDANCE SYSTEM/
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (create from .env.example)
│   ├── database/
│   │   ├── connection.py      # DB engine + session
│   │   └── models.py          # SQLAlchemy ORM models
│   ├── routers/
│   │   ├── auth.py            # Login / JWT
│   │   ├── students.py        # CRUD for students
│   │   ├── enrollment.py      # Biometric enrollment endpoints
│   │   ├── attendance.py      # Mark / verify attendance
│   │   ├── reports.py         # Report generation
│   │   └── settings.py        # System settings + wipe data
│   └── services/
│       ├── face_service.py    # FaceNet AI service
│       ├── palm_service.py    # MediaPipe palm service
│       ├── fingerprint_service.py # WebAuthn fingerprint service
│       └── fusion_service.py  # Multi-modal score fusion
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Students/      # Add, Edit, List, Detail pages
│   │   │   ├── Attendance/    # MarkAttendance, AttendanceList
│   │   │   ├── Enrollment/    # Face, Palm, Fingerprint enroll pages
│   │   │   ├── Reports/       # Reports page
│   │   │   └── Settings/      # Settings + Wipe Data
│   │   └── components/
│   │       ├── SmartWebcamCapture.jsx  # AI bounding box camera
│   │       └── Layout.jsx, Navbar.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## ⚙️ Admin Features

| Feature | Location |
|---------|----------|
| Add / Edit / Delete students | Students menu |
| Re-enroll biometrics | Student Detail → Biometric section |
| View attendance records | Attendance Records |
| Export CSV / PDF reports | Reports |
| Wipe all data | Settings → Danger Zone |

---

## 🛡️ Advanced Security & Anti-Spoofing

To prevent fraud and spoofing (using photos or masks), the system incorporates enterprise-grade liveness checks and duplicate prevention algorithms.

### 1. Liveness Detection (Anti-Spoofing)
- **Face Blink Detection:** Uses MediaPipe FaceLandmarker to calculate the **Eye Aspect Ratio (EAR)** in real-time. The capture button remains locked until the system detects the user blinking at least once (EAR drops below 0.20), preventing photo-based spoofing.
- **Palm Stability Check:** Requires the user to hold their palm steady in the frame for a continuous **2-second progress bar**. Micro-movements of a live hand confirm presence, while also ensuring high-quality, non-blurry captures.
- **Fingerprint Hardware Security:** Relies on the OS-level secure enclave (Touch ID / Windows Hello) which has hardware-based capacitive and subcutaneous liveness sensors built-in.

### 2. Duplicate Biometric Prevention
- During enrollment, the system scans the live face/palm against **all previously enrolled students in the database**.
- If a match exceeds the strict duplicate threshold (Face > 85%, Palm > 95%), the enrollment is **rejected** (HTTP 409 Conflict) and the admin is notified which existing student profile the biometrics belong to.

---

## 🔐 System Security Notes

- Admin authentication uses JWT tokens (stored in `localStorage`)
- Passwords are hashed with **bcrypt**
- WebAuthn fingerprint uses platform authenticator only (Touch ID)
- The "Wipe All Data" function requires typing `DELETE ALL` to confirm

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `MediaPipe failed to initialize` | Run `pip install mediapipe==0.10.14` |
| `No face detected` | Ensure good lighting, look directly at camera |
| `Face enrollment failed` | Only one person should be in frame |
| Frontend won't load | Run `npm run dev` inside the `frontend/` folder |
| Backend 500 error | Check `.env` database credentials; restart backend |
| Touch ID passkey dialog appears | Update to latest code (uses `residentKey: discouraged`) |
