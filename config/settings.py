"""
Configuration settings for SnapClass Attendance System.
Loads environment variables and initializes the Supabase client.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

<<<<<<< HEAD
# Locate directories and load environment variables from config/.env or root .env
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ENV_PATH_CONFIG = CONFIG_DIR / ".env"
ENV_PATH_ROOT = ROOT_DIR / ".env"

if ENV_PATH_CONFIG.exists():
    load_dotenv(dotenv_path=ENV_PATH_CONFIG)
elif ENV_PATH_ROOT.exists():
    load_dotenv(dotenv_path=ENV_PATH_ROOT)
=======
# Locate root directory and load environment variables from .env
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
>>>>>>> fcebf06017d3db8510430498d51002843af0f415
else:
    load_dotenv()

# Supabase Credentials (loaded from .env or environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Flask Server Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

# Initialize the Supabase Client
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("[Config Warning] SUPABASE_URL or SUPABASE_KEY is missing. Check your .env file.")
        supabase = None
except Exception as e:
    print(f"[Config Warning] Supabase client initialization error: {e}")
    supabase = None
