"""
Flask Application and REST API for SnapClass Attendance System.
Connects the modern HTML/CSS/JS frontend to the backend database and AI pipelines.
"""
import os
import io
import base64
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response
from PIL import Image
import numpy as np

# Config and Database
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, supabase
from backend.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_all_students,
    create_student,
    create_subject,
    get_teacher_subjects,
    enroll_student_to_subject,
    unenroll_student_to_subject,
    get_student_subjects,
    get_student_attendance,
    create_attendance,
    get_attendance_for_teacher
)

# AI Pipelines
from backend.pipelines.face_pipeline import (
    predict_attendance,
    get_face_embeddings,
    train_classifier
)
from backend.pipelines.voice_pipeline import (
    get_voice_embedding,
    process_bulk_audio
)

# QR Code Generation
import segno

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
IMG_DIR = BASE_DIR / "img"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "snapclass-super-secret-key-2026")
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB limit for batch photo uploads


# -------------------------------------------------------------
# Frontend Static File Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Serves the main single-page application dashboard."""
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/css/<path:filename>")
def serve_css(filename):
    """Serves CSS stylesheets."""
    return send_from_directory(str(FRONTEND_DIR / "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
    """Serves JavaScript application files."""
    return send_from_directory(str(FRONTEND_DIR / "js"), filename)


@app.route("/img/<path:filename>")
def serve_img(filename):
    """Serves static image assets (e.g. logos)."""
    return send_from_directory(str(IMG_DIR), filename)


# Helper function to decode base64 or file images
def _parse_image_from_request(req, field_name="image"):
    """Extracts a PIL Image from either a multipart file or a base64 DataURL."""
    if field_name in req.files:
        file_obj = req.files[field_name]
        return Image.open(file_obj.stream).convert('RGB')
    
    data = req.get_json(silent=True) or {}
    img_b64 = data.get(field_name) or req.form.get(field_name)
    if img_b64:
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        decoded = base64.b64decode(img_b64)
        return Image.open(io.BytesIO(decoded)).convert('RGB')
    return None


# Helper function to decode audio from request
def _parse_audio_from_request(req, field_name="audio"):
    """Extracts audio bytes from multipart file or base64 DataURL."""
    if field_name in req.files:
        return req.files[field_name].read()
    
    data = req.get_json(silent=True) or {}
    audio_b64 = data.get(field_name) or req.form.get(field_name)
    if audio_b64:
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",", 1)[1]
        return base64.b64decode(audio_b64)
    return None


# -------------------------------------------------------------
# Teacher Authentication Routes
# -------------------------------------------------------------
@app.route("/api/teacher/login", methods=["POST"])
def api_teacher_login():
    """Authenticates teacher with username and password."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    teacher = teacher_login(username, password)
    if teacher:
        # Don't return password hash in response
        teacher_safe = {
            "teacher_id": teacher["teacher_id"],
            "name": teacher["name"],
            "username": teacher["username"]
        }
        return jsonify({"success": True, "teacher": teacher_safe})
    return jsonify({"success": False, "error": "Invalid username or password combo"}), 401


@app.route("/api/teacher/register", methods=["POST"])
def api_teacher_register():
    """Registers a new teacher profile."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    name = (data.get("name") or "").strip()
    password = (data.get("password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not username or not name or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400
    if check_teacher_exists(username):
        return jsonify({"success": False, "error": "Username already taken"}), 409
    if password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match"}), 400

    try:
        create_teacher(username, password, name)
        return jsonify({"success": True, "message": "Successfully created account! You can now log in."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to register teacher: {str(e)}"}), 500


# -------------------------------------------------------------
# Student FaceID Login & Registration Routes
# -------------------------------------------------------------
@app.route("/api/student/login-face", methods=["POST"])
def api_student_login_face():
    """
    Scans student camera snapshot using the face recognition pipeline
    and logs the student in if recognized.
    """
    img = _parse_image_from_request(request, "image")
    if not img:
        return jsonify({"success": False, "error": "No image data provided"}), 400

    img_np = np.array(img)
    try:
        detected, all_ids, num_faces = predict_attendance(img_np)
    except Exception as e:
        return jsonify({"success": False, "error": f"Face recognition error: {str(e)}"}), 500

    if num_faces == 0:
        return jsonify({
            "success": False,
            "code": "NO_FACE",
            "message": "Face not found! Please position your face clearly in the camera center."
        }), 422

    if num_faces > 1:
        return jsonify({
            "success": False,
            "code": "MULTIPLE_FACES",
            "message": "Multiple faces detected. Please make sure only one person is in the frame."
        }), 422

    if detected:
        student_id = list(detected.keys())[0]
        all_students = get_all_students()
        student = next((s for s in all_students if s['student_id'] == student_id), None)
        if student:
            # Exclude raw vector embedding lists from JSON response to save bandwidth
            student_safe = {
                "student_id": student["student_id"],
                "name": student["name"],
                "has_voice": bool(student.get("voice_embedding"))
            }
            return jsonify({"success": True, "student": student_safe})

    return jsonify({
        "success": False,
        "code": "NOT_RECOGNIZED",
        "message": "Face not recognized! If you are a new student, please register your profile below."
    }), 404


@app.route("/api/student/register", methods=["POST"])
def api_student_register():
    """
    Registers a new student profile with face embedding and optional voice embedding.
    """
    name = (request.form.get("name") or "").strip()
    if not name:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"success": False, "error": "Student name is required"}), 400

    img = _parse_image_from_request(request, "image")
    if not img:
        return jsonify({"success": False, "error": "Face photo is required for registration"}), 400

    img_np = np.array(img)
    try:
        encodings = get_face_embeddings(img_np)
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to compute face embedding: {str(e)}"}), 500

    if not encodings:
        return jsonify({
            "success": False,
            "error": "Could not capture distinct facial features. Please ensure good lighting and face the camera directly."
        }), 422

    face_emb = encodings[0].tolist()

    # Optional Voice Embedding
    voice_emb = None
    audio_bytes = _parse_audio_from_request(request, "audio")
    if audio_bytes and len(audio_bytes) > 0:
        try:
            voice_emb = get_voice_embedding(audio_bytes)
        except Exception as e:
            print(f"[Register Warning] Voice embedding extraction error: {e}")

    try:
        response_data = create_student(name, face_embedding=face_emb, voice_embedding=voice_emb)
        if response_data:
            # Retrain the face classifier in background so new student is instantly recognized
            train_classifier()
            student = response_data[0]
            student_safe = {
                "student_id": student["student_id"],
                "name": student["name"],
                "has_voice": bool(voice_emb)
            }
            return jsonify({
                "success": True,
                "student": student_safe,
                "message": f"Profile created successfully! Welcome, {name}."
            })
        return jsonify({"success": False, "error": "Database insert failed"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500


# -------------------------------------------------------------
# Student Dashboard Routes
# -------------------------------------------------------------
@app.route("/api/student/<int:student_id>/subjects", methods=["GET"])
def api_student_subjects(student_id):
    """Returns all enrolled subjects for a student with detailed attendance stats."""
    try:
        enrolled_nodes = get_student_subjects(student_id)
        attendance_logs = get_student_attendance(student_id)

        stats_map = {}
        for log in attendance_logs:
            sid = log['subject_id']
            if sid not in stats_map:
                stats_map[sid] = {"total": 0, "attended": 0}
            stats_map[sid]["total"] += 1
            if log.get("is_present"):
                stats_map[sid]["attended"] += 1

        subjects_list = []
        total_classes_all = 0
        total_attended_all = 0

        for node in enrolled_nodes:
            sub = node.get("subjects") or {}
            sid = sub.get("subject_id")
            stats = stats_map.get(sid, {"total": 0, "attended": 0})
            percentage = round((stats["attended"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0.0

            total_classes_all += stats["total"]
            total_attended_all += stats["attended"]

            subjects_list.append({
                "subject_id": sid,
                "name": sub.get("name", "Unknown Subject"),
                "subject_code": sub.get("subject_code", ""),
                "section": sub.get("section", ""),
                "total_classes": stats["total"],
                "attended_classes": stats["attended"],
                "percentage": percentage
            })

        overall_percentage = round((total_attended_all / total_classes_all * 100), 1) if total_classes_all > 0 else 0.0

        return jsonify({
            "success": True,
            "subjects": subjects_list,
            "summary": {
                "total_enrolled": len(subjects_list),
                "total_classes": total_classes_all,
                "total_attended": total_attended_all,
                "overall_percentage": overall_percentage
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/student/enroll", methods=["POST"])
def api_student_enroll():
    """Enrolls a student in a subject using the subject code."""
    data = request.get_json() or {}
    student_id = data.get("student_id")
    subject_code = (data.get("subject_code") or "").strip()

    if not student_id or not subject_code:
        return jsonify({"success": False, "error": "Student ID and Subject Code are required"}), 400

    res = supabase.table('subjects').select('subject_id, name, subject_code').eq('subject_code', subject_code).execute()
    if not res.data:
        return jsonify({"success": False, "error": f"Subject code '{subject_code}' not found."}), 404

    subject = res.data[0]
    subject_id = subject['subject_id']

    check = supabase.table('subject_students').select('*').eq('subject_id', subject_id).eq('student_id', student_id).execute()
    if check.data:
        return jsonify({"success": False, "error": f"You are already enrolled in {subject['name']}."}), 409

    try:
        enroll_student_to_subject(student_id, subject_id)
        return jsonify({
            "success": True,
            "message": f"Successfully enrolled in {subject['name']} ({subject['subject_code']})!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/student/unenroll", methods=["POST"])
def api_student_unenroll():
    """Unenrolls a student from a subject."""
    data = request.get_json() or {}
    student_id = data.get("student_id")
    subject_id = data.get("subject_id")

    if not student_id or not subject_id:
        return jsonify({"success": False, "error": "Student ID and Subject ID are required"}), 400

    try:
        unenroll_student_to_subject(student_id, subject_id)
        return jsonify({"success": True, "message": "Successfully unenrolled from the course."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------
# Quick Auto-Enroll Helper Route
# -------------------------------------------------------------
@app.route("/api/subject/info/<subject_code>", methods=["GET"])
def api_subject_info(subject_code):
    """Looks up subject details by subject code for quick QR/link enrollment."""
    res = supabase.table('subjects').select('subject_id, name, subject_code, section').eq('subject_code', subject_code).execute()
    if not res.data:
        return jsonify({"success": False, "error": "Subject not found"}), 404
    return jsonify({"success": True, "subject": res.data[0]})


# -------------------------------------------------------------
# Teacher Dashboard & Subjects Management Routes
# -------------------------------------------------------------
@app.route("/api/teacher/<int:teacher_id>/subjects", methods=["GET"])
def api_teacher_subjects(teacher_id):
    """Retrieves all subjects for a teacher."""
    try:
        subjects = get_teacher_subjects(teacher_id)
        return jsonify({"success": True, "subjects": subjects})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/teacher/subjects", methods=["POST"])
def api_teacher_create_subject():
    """Creates a new subject assigned to the teacher."""
    data = request.get_json() or {}
    teacher_id = data.get("teacher_id")
    subject_code = (data.get("subject_code") or "").strip()
    name = (data.get("name") or "").strip()
    section = (data.get("section") or "").strip()

    if not teacher_id or not subject_code or not name or not section:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        res = create_subject(subject_code, name, section, teacher_id)
        return jsonify({"success": True, "subject": res, "message": "Subject created successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/subject/<subject_code>/qr", methods=["GET"])
def api_subject_qr(subject_code):
    """Generates a QR code image for enrolling via join-code link."""
    host = request.host_url.rstrip("/")
    join_url = f"{host}/?join-code={subject_code}"
    
    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind="png", scale=8, border=2)
    out.seek(0)
    
    return Response(out.getvalue(), mimetype="image/png")


# -------------------------------------------------------------
# AI Attendance Scanning Routes (Face & Voice)
# -------------------------------------------------------------
@app.route("/api/attendance/face-scan", methods=["POST"])
def api_attendance_face_scan():
    """
    Scans one or more classroom photos for student faces,
    identifies recognized enrolled students, and produces a preview.
    """
    subject_id = request.form.get("subject_id")
    if not subject_id:
        data = request.get_json(silent=True) or {}
        subject_id = data.get("subject_id")

    if not subject_id:
        return jsonify({"success": False, "error": "Subject ID is required"}), 400

    subject_id = int(subject_id)

    # Collect images from files or JSON
    images = []
    if "images" in request.files:
        files = request.files.getlist("images")
        for f in files:
            try:
                images.append(Image.open(f.stream).convert('RGB'))
            except Exception as e:
                print(f"[Photo Parse Error]: {e}")
    else:
        # Base64 array in JSON
        data = request.get_json(silent=True) or {}
        b64_list = data.get("images") or []
        for item in b64_list:
            try:
                if "," in item:
                    item = item.split(",", 1)[1]
                decoded = base64.b64decode(item)
                images.append(Image.open(io.BytesIO(decoded)).convert('RGB'))
            except Exception as e:
                print(f"[Base64 Image Parse Error]: {e}")

    if not images:
        return jsonify({"success": False, "error": "Please provide at least one classroom photo."}), 400

    all_detected_ids = {}

    for idx, img in enumerate(images):
        img_np = np.array(img)
        try:
            detected, _, _ = predict_attendance(img_np)
            if detected:
                for sid in detected.keys():
                    student_id = int(sid)
                    all_detected_ids.setdefault(student_id, []).append(f"Photo {idx + 1}")
        except Exception as e:
            print(f"[Face Scan Photo {idx+1} Error]: {e}")

    # Fetch enrolled students
    enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', subject_id).execute()
    enrolled_students = enrolled_res.data or []

    if not enrolled_students:
        return jsonify({"success": False, "error": "No students are enrolled in this subject yet."}), 404

    results = []
    attendance_to_log = []
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for node in enrolled_students:
        student = node.get('students') or {}
        sid = int(student.get('student_id', 0))
        sources = all_detected_ids.get(sid, [])
        is_present = len(sources) > 0

        results.append({
            "name": student.get('name', 'Unknown'),
            "student_id": sid,
            "source": ", ".join(sources) if is_present else "-",
            "is_present": is_present,
            "status": "Present" if is_present else "Absent"
        })

        attendance_to_log.append({
            "student_id": sid,
            "subject_id": subject_id,
            "timestamp": current_timestamp,
            "is_present": bool(is_present)
        })

    return jsonify({
        "success": True,
        "results": results,
        "logs": attendance_to_log,
        "summary": {
            "total_enrolled": len(results),
            "present_count": sum(1 for r in results if r["is_present"]),
            "absent_count": sum(1 for r in results if not r["is_present"]),
            "photos_scanned": len(images)
        }
    })


@app.route("/api/attendance/voice-scan", methods=["POST"])
def api_attendance_voice_scan():
    """
    Analyzes classroom audio snippet against enrolled student voice profiles.
    """
    subject_id = request.form.get("subject_id")
    if not subject_id:
        data = request.get_json(silent=True) or {}
        subject_id = data.get("subject_id")

    if not subject_id:
        return jsonify({"success": False, "error": "Subject ID is required"}), 400

    subject_id = int(subject_id)
    audio_bytes = _parse_audio_from_request(request, "audio")

    if not audio_bytes:
        return jsonify({"success": False, "error": "Audio recording is required"}), 400

    # Fetch enrolled students
    enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', subject_id).execute()
    enrolled_students = enrolled_res.data or []

    if not enrolled_students:
        return jsonify({"success": False, "error": "No students enrolled in this course"}), 404

    candidates_dict = {
        s['students']['student_id']: s['students']['voice_embedding']
        for s in enrolled_students if s.get('students') and s['students'].get('voice_embedding')
    }

    if not candidates_dict:
        return jsonify({
            "success": False,
            "error": "None of the students enrolled in this course have voice profiles registered."
        }), 422

    try:
        detected_scores = process_bulk_audio(audio_bytes, candidates_dict)
    except Exception as e:
        return jsonify({"success": False, "error": f"Audio processing error: {str(e)}"}), 500

    results = []
    attendance_to_log = []
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for node in enrolled_students:
        student = node.get('students') or {}
        sid = int(student.get('student_id', 0))
        score = detected_scores.get(sid, 0.0)
        is_present = bool(score > 0)

        results.append({
            "name": student.get('name', 'Unknown'),
            "student_id": sid,
            "source": f"Confidence: {round(score * 100, 1)}%" if is_present else "-",
            "is_present": is_present,
            "status": "Present" if is_present else "Absent"
        })

        attendance_to_log.append({
            "student_id": sid,
            "subject_id": subject_id,
            "timestamp": current_timestamp,
            "is_present": bool(is_present)
        })

    return jsonify({
        "success": True,
        "results": results,
        "logs": attendance_to_log,
        "summary": {
            "total_enrolled": len(results),
            "present_count": sum(1 for r in results if r["is_present"]),
            "absent_count": sum(1 for r in results if not r["is_present"])
        }
    })


@app.route("/api/attendance/confirm", methods=["POST"])
def api_attendance_confirm():
    """Batch-inserts verified attendance records into the Supabase attendance_logs table."""
    data = request.get_json() or {}
    logs = data.get("logs") or []

    if not logs:
        return jsonify({"success": False, "error": "No attendance log records provided"}), 400

    try:
        res = create_attendance(logs)
        return jsonify({"success": True, "message": f"Successfully logged attendance for {len(logs)} students!"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Database sync failed: {str(e)}"}), 500


# -------------------------------------------------------------
# Teacher Attendance Records & Analytics Routes
# -------------------------------------------------------------
@app.route("/api/teacher/<int:teacher_id>/attendance-records", methods=["GET"])
def api_teacher_attendance_records(teacher_id):
    """
    Retrieves and summarizes attendance session logs for a teacher.
    """
    try:
        records = get_attendance_for_teacher(teacher_id) or []
        session_map = {}

        for r in records:
            ts = r.get("timestamp")
            if not ts:
                continue
            
            sub = r.get("subjects") or {}
            sub_id = sub.get("subject_id")
            key = f"{ts}_{sub_id}"

            if key not in session_map:
                try:
                    formatted_time = datetime.fromisoformat(ts).strftime("%b %d, %Y - %I:%M %p")
                except Exception:
                    formatted_time = ts

                session_map[key] = {
                    "timestamp": ts,
                    "formatted_time": formatted_time,
                    "subject_name": sub.get("name", "Unknown"),
                    "subject_code": sub.get("subject_code", ""),
                    "present_count": 0,
                    "total_count": 0
                }

            session_map[key]["total_count"] += 1
            if r.get("is_present"):
                session_map[key]["present_count"] += 1

        sessions = list(session_map.values())
        sessions.sort(key=lambda s: s["timestamp"], reverse=True)

        return jsonify({"success": True, "sessions": sessions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/teacher/<int:teacher_id>/analytics", methods=["GET"])
def api_teacher_analytics(teacher_id):
    """
    Generates structured analytics data for Chart.js in the frontend:
    - Attendance rates per subject (Bar Chart)
    - Trend across recent attendance sessions (Line Chart)
    - Overall attendance distribution (Doughnut Chart)
    """
    try:
        subjects = get_teacher_subjects(teacher_id) or []
        records = get_attendance_for_teacher(teacher_id) or []

        # 1. Subject Breakdown
        sub_stats = {s["subject_id"]: {"name": s["name"], "code": s["subject_code"], "present": 0, "total": 0} for s in subjects}
        total_present = 0
        total_absent = 0

        # 2. Timeline Breakdown (chronological sessions)
        timeline_map = {}

        for r in records:
            sid = r.get("subjects", {}).get("subject_id")
            is_pres = bool(r.get("is_present"))

            if sid in sub_stats:
                sub_stats[sid]["total"] += 1
                if is_pres:
                    sub_stats[sid]["present"] += 1

            if is_pres:
                total_present += 1
            else:
                total_absent += 1

            ts = r.get("timestamp")
            if ts:
                # Group by date YYYY-MM-DD
                date_key = ts.split("T")[0]
                if date_key not in timeline_map:
                    timeline_map[date_key] = {"present": 0, "total": 0}
                timeline_map[date_key]["total"] += 1
                if is_pres:
                    timeline_map[date_key]["present"] += 1

        # Chart 1: Subject labels & percentage
        subject_labels = []
        subject_percentages = []
        for sid, s in sub_stats.items():
            subject_labels.append(s["code"] or s["name"])
            pct = round((s["present"] / s["total"] * 100), 1) if s["total"] > 0 else 0.0
            subject_percentages.append(pct)

        # Chart 2: Timeline labels & rates
        timeline_sorted = sorted(timeline_map.items())
        trend_labels = [k for k, _ in timeline_sorted[-10:]]  # Last 10 days
        trend_values = [round((v["present"] / v["total"] * 100), 1) if v["total"] > 0 else 0.0 for _, v in timeline_sorted[-10:]]

        return jsonify({
            "success": True,
            "subject_chart": {
                "labels": subject_labels,
                "values": subject_percentages
            },
            "trend_chart": {
                "labels": trend_labels,
                "values": trend_values
            },
            "doughnut_chart": {
                "labels": ["Present", "Absent"],
                "values": [total_present, total_absent]
            },
            "totals": {
                "total_students_enrolled": sum(s.get("total_students", 0) for s in subjects),
                "total_subjects": len(subjects),
                "total_attendance_logs": len(records),
                "average_attendance": round((total_present / (total_present + total_absent) * 100), 1) if (total_present + total_absent) > 0 else 0.0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def create_app():
    """Factory function for testing or WSGI servers."""
    return app


if __name__ == "__main__":
    print(f"[*] Starting SnapClass Server on http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
