"""
SnapClass - AI-Powered Classroom Attendance System
Root entrypoint for running the Flask application server.
"""
from backend.app import app
from config.settings import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == "__main__":
    print(f"[*] Starting SnapClass Server on http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)