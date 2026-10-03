# Setup Guide — Multi-Modal Attendance System

This guide walks you through installing and running the system on a **macOS or Windows laptop** from scratch.

---

## Prerequisites

Install the following before proceeding:

| Software | Version | Download |
|---|---|---|
| Python | 3.10 or 3.11 | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| MySQL | 8.0+ | https://mysql.com |
| Git | Any | https://git-scm.com |
| CMake | Latest | https://cmake.org (needed for dlib/face_recognition) |

### macOS — Install CMake and dlib dependencies
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install cmake and dependencies for dlib
brew install cmake
brew install boost
```

### Windows — Install CMake and Visual Studio Build Tools
1. Download CMake from https://cmake.org/download/
2. Install **Visual Studio Build Tools** with "Desktop development with C++" workload.
3. Restart your computer after installation.

---

## Step 1 — Clone / Download the Project

If you have Git:
```bash
git clone <your-repo-url>
cd "MULTI-MODAL ATTENDANCE SYSTEM"
```

Or just extract the ZIP file to a folder called `MULTI-MODAL ATTENDANCE SYSTEM`.

---

## Step 2 — Database Setup

### 2.1 — Start MySQL Server

**macOS (with Homebrew):**
```bash
brew services start mysql
```

**Windows:** Open MySQL Workbench or run MySQL from Services.

### 2.2 — Create the Database

```bash
mysql -u root -p < database/schema.sql
```

Enter your MySQL root password when prompted.

This will:
- Create the `attendance_db` database
- Create all tables
- Insert the default admin account (`admin` / `admin123`)
- Insert default system settings
- Insert 5 sample students for testing

### 2.3 — Verify Database

```bash
mysql -u root -p -e "USE attendance_db; SHOW TABLES;"
```

Expected output:
```
+-------------------------+
| Tables_in_attendance_db |
+-------------------------+
| admins                  |
| attendance              |
| face_templates          |
| fingerprint_templates   |
| palm_templates          |
| students                |
| system_settings         |
+-------------------------+
```

---

## Step 3 — Backend Setup

### 3.1 — Navigate to backend folder

```bash
cd backend
```

### 3.2 — Create Python virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3.3 — Install Python dependencies

> ⚠️ `face_recognition` requires `dlib` which compiles C++ code. This takes **5–15 minutes**. Be patient.

```bash
pip install -r requirements.txt
```

**If face_recognition fails on macOS:**
```bash
pip install cmake
pip install dlib
pip install face_recognition
```

**If face_recognition fails on Windows:**
Download pre-built dlib wheel from:
https://github.com/z-mahmud22/Dlib_Windows_Python3.x

```bash
pip install dlib-19.24.1-cp310-cp310-win_amd64.whl  # match your Python version
pip install face_recognition
```

### 3.4 — Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials:
```ini
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/attendance_db
SECRET_KEY=change-this-to-a-random-64-char-string
```

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.5 — Start the backend server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 3.6 — Verify backend

Open your browser: **http://localhost:8000/docs**

You should see the Swagger UI with all API endpoints.

---

## Step 4 — Frontend Setup

Open a **new terminal** (keep the backend running).

### 4.1 — Navigate to frontend folder

```bash
cd frontend
```

### 4.2 — Install Node packages

```bash
npm install
```

### 4.3 — Start the development server

```bash
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in 300ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

---

## Step 5 — Open the Application

Open your browser and go to: **http://localhost:5173**

Login with:
- **Username:** `admin`
- **Password:** `admin123`

---

## Webcam Permissions

The browser will ask for webcam access on the Enrollment and Attendance pages.

- Click **Allow** when prompted.
- If denied accidentally: Chrome → Settings → Privacy → Camera → Allow localhost.

---

## Folder Structure After Setup

```
backend/
├── venv/            ← Python virtual environment (auto-created)
├── .env             ← Your config (never commit this)
├── main.py
├── requirements.txt
└── ...

frontend/
├── node_modules/    ← npm packages (auto-created)
├── src/
└── ...

database/
└── schema.sql
```

---

## Running the System Daily

Every time you want to run the system:

**Terminal 1 — Backend:**
```bash
cd "MULTI-MODAL ATTENDANCE SYSTEM/backend"
source venv/bin/activate   # (macOS) or venv\Scripts\activate (Windows)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd "MULTI-MODAL ATTENDANCE SYSTEM/frontend"
npm run dev
```

Then open **http://localhost:5173**.

---

## LAN Access (Other Students on Same Network)

To let other computers on your network access the system:

1. Find your laptop's IP:
   - macOS: `ifconfig | grep "inet " | grep -v 127`
   - Windows: `ipconfig` → look for IPv4 Address

2. Share these URLs with classmates:
   ```
   http://YOUR_IP:5173    ← Frontend
   http://YOUR_IP:8000    ← Backend API
   ```

3. Update `frontend/vite.config.js` proxy if needed.

---

## Troubleshooting

### "Module not found: face_recognition"
```bash
pip install face_recognition
```
If it fails, install cmake first: `pip install cmake`

### "Access denied for user 'root'@'localhost'"
Wrong MySQL password in `.env`. Double-check your MySQL root password.

### "Port 8000 already in use"
```bash
uvicorn main:app --reload --port 8001
```
And update `frontend/vite.config.js` proxy target to port 8001.

### Webcam not detected
- Check that your browser has camera permissions for localhost.
- Try a different browser (Chrome works best).

### MediaPipe install fails
```bash
pip install mediapipe --upgrade
```

---

## Production Deployment Notes

For a real classroom deployment (not just demo):

1. Use a proper MySQL password (not empty/default).
2. Change `SECRET_KEY` to a long random string.
3. Enable HTTPS using nginx + Let's Encrypt.
4. Set `CORS` in `main.py` to only allow your frontend domain.
5. Encrypt biometric templates at rest.
6. Set up MySQL backups.
