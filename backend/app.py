"""
SnapClass Flask Application (Compatibility Module).
Delegates to backend.main where the full Flask REST API and routing is defined.
"""
from backend.main import (
    app,
    create_app,
    health_check,
    api_teacher_login,
    api_teacher_register,
    api_student_login_face,
    api_student_register,
    api_student_subjects,
    api_student_enroll,
    api_student_unenroll,
    api_subject_info,
    api_teacher_subjects,
    api_teacher_create_subject,
    api_subject_qr,
    api_attendance_face_scan,
    api_attendance_voice_scan,
    api_attendance_confirm,
    api_teacher_attendance_records,
    api_teacher_analytics,
)

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
