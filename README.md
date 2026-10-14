# 📸 SnapClass - AI-Powered Attendance Management System

<p align="center">
  <img src="https://i.ibb.co/YTYGn5qV/logo.png" width="120" alt="SnapClass Logo" />
</p>

<p align="center">
  <strong>Modern HTML5 & CSS3 Frontend • Flask REST API • Face Recognition • Voice Analysis • Supabase</strong>
</p>

<p align="center">
  Author: <b>Hamid Ansari</b> (AI/ML Developer | B.Tech CSE AI)
</p>

---

## 🚀 Overview

**SnapClass Attendance System** is an enterprise-grade, AI-driven attendance management web platform. Originally prototyped in Streamlit, the system has been transformed into a production-ready **HTML5 + Vanilla CSS3 + JavaScript frontend** communicating via RESTful API routes with a high-performance **Python/Flask backend**.

The core AI pipelines (**dlib 128-d face recognition**, **Resemblyzer acoustic voice embeddings**) and **Supabase cloud PostgreSQL** database logic remain **100% intact and preserved**.

---

## 📁 Clean Architecture & Folder Structure

```text
├── frontend/
│   ├── index.html            # Semantic HTML5 single-page application
│   ├── css/
│   │   └── style.css         # Modern, responsive CSS (Flexbox/Grid, Glassmorphism, Animations)
│   └── js/
│       ├── app.js            # Frontend application controller, Camera/Audio streams, REST API calls
│       └── charts.js         # Interactive Chart.js analytics visualizations
│
├── backend/
│   ├── __init__.py           # Backend package exports
│   ├── app.py                # Flask application, REST routes, static file server
│   ├── db.py                 # Pure Supabase database logic, queries & auth (preserved)
│   └── pipelines/
│       ├── __init__.py
│       ├── face_pipeline.py  # dlib face detection, landmark predictor, linear SVM & distance matching
│       └── voice_pipeline.py # Resemblyzer d-vector embeddings, librosa silence splitting & cosine matching
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Environment variables, Supabase credentials & server configs
│
├── img/
│   └── logo.png              # SnapClass logo asset
│
├── app.py                    # Root entrypoint to run the Flask application
├── requirements.txt          # Cleaned dependencies (Streamlit removed, Flask & dotenv added)
├── .env                      # Supabase URL & Service Key
└── README.md                 # Complete documentation
```

---

## ✨ Features

### 👨‍🎓 Student Portal
- **FaceID Login**: Direct webcam access via HTML5 `getUserMedia`. Captures high-res face frames and authenticates via Euclidean distance matching against registered embeddings.
- **Dynamic Profile Registration**: Automatic detection for new students with real-time feedback, name input, and immediate classifier retraining.
- **Optional Voice Enrollment**: Live microphone capture using `MediaRecorder` API to enroll acoustic voiceprints for voice attendance.
- **Enrolled Course Dashboard**: Displays total sessions held, attended count, attendance rate percentage, and unenroll options.
- **Join by Code**: Manual subject code enrollment or **Instant Auto-Enrollment** via QR code / link (`/?join-code=<code>`).

### 👨‍🏫 Teacher Portal
- **Secure Authentication**: Teacher registration and bcrypt-hashed password authentication.
- **Subject Management**: Create courses (Subject Code, Name, Section) and generate printable / shareable **QR Codes** using `segno`.
- **Classroom AI Attendance (Face Scan)**:
  - Add classroom photos via live camera snapshots or batch file uploads.
  - Interactive photo gallery with individual removal and batch clearing.
  - Deep face scanning across all uploaded photos with attendance review table before saving.
- **Classroom Voice Attendance**:
  - Live microphone recording of roll calls or audio file upload.
  - Audio silence splitting (`top_db=30`) and cosine similarity speaker verification.
- **Attendance Records & Interactive Chart.js Analytics**:
  - Historical session logs table.
  - **Bar Chart**: Attendance rate across all subjects.
  - **Line Chart**: Attendance timeline trends over sessions.
  - **Doughnut Chart**: Overall Present vs. Absent student distribution.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, Modern Vanilla CSS3 (Flexbox/Grid), JavaScript (ES6+), Chart.js |
| **Backend** | Python 3.11, Flask 3.1, RESTful JSON API |
| **Database & Auth** | Supabase (Cloud PostgreSQL), bcrypt |
| **Face Recognition** | dlib, `face_recognition_models` (ResNet-34 128D), Scikit-Learn (Linear SVC) |
| **Voice Recognition** | Resemblyzer (GE2E d-vectors), librosa audio processing, PyTorch |
| **QR Code Engine** | Segno QR code generator |

---

## 🔌 API Route Reference

### Authentication & Profiles
- `POST /api/teacher/login`: Authenticates teacher credentials.
- `POST /api/teacher/register`: Creates new teacher account.
- `POST /api/student/login-face`: Receives base64/multipart face image, predicts student identity.
- `POST /api/student/register`: Creates student record with face descriptor and optional voice embedding.

### Student Endpoints
- `GET /api/student/<student_id>/subjects`: Fetches enrolled subjects with attendance statistics.
- `POST /api/student/enroll`: Enrolls student in subject via subject code.
- `POST /api/student/unenroll`: Unenrolls student from subject.
- `GET /api/subject/info/<subject_code>`: Checks subject validity for auto-enroll link.

### Teacher Endpoints
- `GET /api/teacher/<teacher_id>/subjects`: Lists teacher's courses with student counts.
- `POST /api/teacher/subjects`: Creates new course.
- `GET /api/subject/<subject_code>/qr`: Generates PNG QR code for join links.
- `POST /api/attendance/face-scan`: Scans classroom photos and generates attendance preview.
- `POST /api/attendance/voice-scan`: Scans audio recording and matches voiceprints.
- `POST /api/attendance/confirm`: Commits verified attendance records to Supabase.
- `GET /api/teacher/<teacher_id>/attendance-records`: Returns historical attendance logs.
- `GET /api/teacher/<teacher_id>/analytics`: Aggregates metrics for Chart.js dashboards.

---

## 🚀 How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Ensure `.env` contains your Supabase credentials:
```env
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-key"
```

### 3. Launch the Server
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```
