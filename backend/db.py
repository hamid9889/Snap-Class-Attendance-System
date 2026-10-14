"""
Database access layer for SnapClass Attendance System.
All Supabase integration and query logic preserved identically from original implementation.
"""
from config.settings import supabase
import bcrypt


def hash_pass(pwd: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pass(pwd: str, hashed: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username: str) -> bool:
    """Check for unique username, returns True if username is already taken."""
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username: str, password: str, name: str):
    """Registers a new teacher record with hashed password."""
    data = {"username": username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str):
    """Authenticates teacher credentials and returns the record if valid."""
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None


def get_all_students():
    """Fetches all registered student profiles."""
    response = supabase.table('students').select("*").execute()
    return response.data


def create_student(new_name: str, face_embedding=None, voice_embedding=None):
    """Creates a new student with optional face and voice embeddings."""
    data = {'name': new_name, 'face_embedding': face_embedding, "voice_embedding": voice_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data


def create_subject(subject_code: str, name: str, section: str, teacher_id: int):
    """Creates a new course/subject assigned to a teacher."""
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data


def get_teacher_subjects(teacher_id: int):
    """Retrieves all subjects for a teacher including student counts and session counts."""
    response = supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subjects = response.data or []

    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance = sub.get('attendance_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        sub['total_classes'] = unique_sessions

        sub.pop('subject_students', None)
        sub.pop('subject_student', None)
        sub.pop('attendance_logs', None)

    return subjects


def enroll_student_to_subject(student_id: int, subject_id: int):
    """Enrolls a student in a specific subject."""
    data = {'student_id': student_id, "subject_id": subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id: int, subject_id: int):
    """Unenrolls a student from a specific subject."""
    response = supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data


def get_student_subjects(student_id: int):
    """Retrieves all subjects a student is currently enrolled in."""
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data or []


def get_student_attendance(student_id: int):
    """Fetches all attendance records for a specific student."""
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data or []


def create_attendance(logs: list):
    """Batch inserts attendance log records into Supabase."""
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data


def get_attendance_for_teacher(teacher_id: int):
    """Retrieves attendance records for all subjects taught by the teacher."""
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data or []
