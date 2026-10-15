"""
SnapClass Attendance System - Configuration Settings
=====================================================
Centralizes environment variables, Supabase credentials, and Flask server options.
Optimized for local execution and production deployment on Render and Vercel.

Environment Loading Priority:
1. System environment variables (Render / Vercel dashboard)
2. config/.env
3. Root .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Project directory paths
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ENV_PATH_CONFIG = CONFIG_DIR / ".env"
ENV_PATH_ROOT = ROOT_DIR / ".env"

# Load environment variables (.env files if present)
if ENV_PATH_CONFIG.exists():
    load_dotenv(dotenv_path=ENV_PATH_CONFIG)
elif ENV_PATH_ROOT.exists():
    load_dotenv(dotenv_path=ENV_PATH_ROOT)
else:
    load_dotenv()

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Flask Server & Security Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("SECRET_KEY", "snapclass-super-secret-key-2026")

# Initialize the Supabase Client
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("[Config Warning] SUPABASE_URL or SUPABASE_KEY is missing. Check your environment settings.")
        supabase = None
except Exception as e:
    print(f"[Config Warning] Supabase client initialization error: {e}")
    supabase = None
