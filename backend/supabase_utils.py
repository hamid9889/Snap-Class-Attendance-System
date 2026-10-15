"""
SnapClass Attendance System - Supabase Utilities & Database Layer
==================================================================
Handles all database operations, table queries, and password hashing
using the official Supabase Python client.

Separates database access logic completely from HTTP route handling.
"""
from typing import List, Dict, Any, Optional
import bcrypt
from config.settings import supabase, SUPABASE_URL, SUPABASE_KEY


def get_supabase_client():
    """
    Returns the initialized Supabase client instance.
    Raises RuntimeError if the client could not be initialized due to missing credentials.
    """
    if supabase is None:
        raise RuntimeError(
            "Supabase client is uninitialized. Verify that SUPABASE_URL and "
            "SUPABASE_KEY are properly configured in config/.env or deployment environment."
        )
    return supabase


# ==============================================================================
# PASSWORD HASHING UTILITIES (bcrypt)
# ==============================================================================
def hash_pass(pwd: str) -> str:
    """
    Hashes a plaintext password string using bcrypt with a generated salt.
    """
    return bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_pass(pwd: str, hashed: str) -> bool:
    """
    Verifies a plaintext password string against a bcrypt-hashed string.
    """
    try:
        return bcrypt.checkpw(pwd.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ==============================================================================
# TEACHER ACCOUNTS & AUTHENTICATION
# ==============================================================================
def check_teacher_exists(username: str) -> bool:
    """
    Checks if a teacher username already exists in the database.
    Returns True if taken, False otherwise.
    """
    client = get_supabase_client()
    response = client.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username: str, password: str, name: str) -> List[Dict[str, Any]]:
    """
    Registers a new teacher record with bcrypt-hashed credentials.
    """
    client = get_supabase_client()
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name
    }
    response = client.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates teacher credentials and returns the teacher profile dictionary if valid.
    """
    client = get_supabase_client()
    response = client.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher.get("password", "")):
            return teacher
    return None


# ==============================================================================
# STUDENT PROFILES & ENROLLMENT
# ==============================================================================
def get_all_students() -> List[Dict[str, Any]]:
    """
    Fetches all registered students from the 'students' table.
    """
    client = get_supabase_client()
    response = client.table("students").select("*").execute()
    return response.data or []


def create_student(
    new_name: str,
    face_embedding: Optional[List[float]] = None,
    voice_embedding: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Creates a new student record with biometric face and/or voice embeddings.
    """
    client = get_supabase_client()
    data = {
        "name": new_name,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding
    }
    response = client.table("students").insert(data).execute()
    return response.data


def get_enrolled_students(subject_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all enrolled students with their profile info for a specific subject.
    """
    client = get_supabase_client()
    response = client.table("subject_students").select("*, students(*)").eq("subject_id", subject_id).execute()
    return response.data or []


def enroll_student_to_subject(student_id: int, subject_id: int) -> List[Dict[str, Any]]:
    """
    Enrolls a student in a course/subject.
    """
    client = get_supabase_client()
    data = {"student_id": student_id, "subject_id": subject_id}
    response = client.table("subject_students").insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id: int, subject_id: int) -> List[Dict[str, Any]]:
    """
    Removes a student enrollment from a subject.
    """
    client = get_supabase_client()
    response = (
        client.table("subject_students")
        .delete()
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    return response.data


def check_student_enrolled(subject_id: int, student_id: int) -> bool:
    """
    Checks if a student is already enrolled in a given subject.
    """
    client = get_supabase_client()
    response = (
        client.table("subject_students")
        .select("*")
        .eq("subject_id", subject_id)
        .eq("student_id", student_id)
        .execute()
    )
    return len(response.data) > 0


def get_student_subjects(student_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all subjects a student is enrolled in, joined with subject details.
    """
    client = get_supabase_client()
    response = client.table("subject_students").select("*, subjects(*)").eq("student_id", student_id).execute()
    return response.data or []


# ==============================================================================
# SUBJECT / COURSE MANAGEMENT
# ==============================================================================
def create_subject(subject_code: str, name: str, section: str, teacher_id: int) -> List[Dict[str, Any]]:
    """
    Creates a new subject under a teacher.
    """
    client = get_supabase_client()
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    response = client.table("subjects").insert(data).execute()
    return response.data


def get_subject_by_code(subject_code: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a subject record by its unique alphanumeric subject_code.
    """
    client = get_supabase_client()
    response = (
        client.table("subjects")
        .select("subject_id, name, subject_code, section, teacher_id")
        .eq("subject_code", subject_code)
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def get_teacher_subjects(teacher_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all subjects for a teacher including student counts and session counts.
    """
    client = get_supabase_client()
    response = (
        client.table("subjects")
        .select("*, subject_students(count), attendance_logs(timestamp)")
        .eq("teacher_id", teacher_id)
        .execute()
    )
    subjects = response.data or []

    for sub in subjects:
        sub["total_students"] = (
            sub.get("subject_students", [{}])[0].get("count", 0)
            if sub.get("subject_students")
            else 0
        )
        attendance = sub.get("attendance_logs", [])
        unique_sessions = len(set(log["timestamp"] for log in attendance))
        sub["total_classes"] = unique_sessions

        # Clean nested join structures for clean JSON response
        sub.pop("subject_students", None)
        sub.pop("subject_student", None)
        sub.pop("attendance_logs", None)

    return subjects


# ==============================================================================
# ATTENDANCE LOGGING & ANALYTICS
# ==============================================================================
def create_attendance(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch inserts attendance log records into Supabase.
    """
    client = get_supabase_client()
    response = client.table("attendance_logs").insert(logs).execute()
    return response.data


def get_student_attendance(student_id: int) -> List[Dict[str, Any]]:
    """
    Fetches attendance logs for a student with associated subject metadata.
    """
    client = get_supabase_client()
    response = client.table("attendance_logs").select("*, subjects(*)").eq("student_id", student_id).execute()
    return response.data or []


def get_attendance_for_teacher(teacher_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves attendance records across all subjects taught by a specific teacher.
    """
    client = get_supabase_client()
    response = (
        client.table("attendance_logs")
        .select("*, subjects!inner(*)")
        .eq("subjects.teacher_id", teacher_id)
        .execute()
    )
    return response.data or []
