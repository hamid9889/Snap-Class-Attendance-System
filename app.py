"""
<<<<<<< HEAD
SnapClass - AI-Powered Classroom Attendance System
Root entrypoint for running the Flask application server.
"""
from backend.app import app
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == "__main__":
    print(f"[*] Starting SnapClass Server on http://{FLASK_HOST}:{FLASK_PORT}")
=======
SnapClass - Modern AI Attendance Management System
Main entry point for starting the Flask server.
"""
import sys
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app import app
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == "__main__":
    print("=" * 60)
    print("  SNAPCLASS ATTENDANCE SYSTEM - MODERN WEB APPLICATION")
    print(f"  Access UI at: http://localhost:{FLASK_PORT}")
    print("=" * 60)
>>>>>>> fcebf06017d3db8510430498d51002843af0f415
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)