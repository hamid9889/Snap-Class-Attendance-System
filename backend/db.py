"""
Database access layer for SnapClass Attendance System.
All Supabase utilities and query operations are housed in backend.supabase_utils.
This module re-exports them to preserve backward compatibility.
"""
from backend.supabase_utils import (
    supabase,
    get_supabase_client,
    hash_pass,
    check_pass,
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_all_students,
    create_student,
    get_enrolled_students,
    create_subject,
    get_subject_by_code,
    get_teacher_subjects,
    enroll_student_to_subject,
    unenroll_student_to_subject,
    check_student_enrolled,
    get_student_subjects,
    get_student_attendance,
    create_attendance,
    get_attendance_for_teacher,
)

__all__ = [
    "supabase",
    "get_supabase_client",
    "hash_pass",
    "check_pass",
    "check_teacher_exists",
    "create_teacher",
    "teacher_login",
    "get_all_students",
    "create_student",
    "get_enrolled_students",
    "create_subject",
    "get_subject_by_code",
    "get_teacher_subjects",
    "enroll_student_to_subject",
    "unenroll_student_to_subject",
    "check_student_enrolled",
    "get_student_subjects",
    "get_student_attendance",
    "create_attendance",
    "get_attendance_for_teacher",
]
