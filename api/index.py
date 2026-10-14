"""
Vercel Serverless Function Entry Point for SnapClass.
Exposes the Flask WSGI 'app' instance.
"""
import sys
from pathlib import Path

# Add project root directory to sys.path so backend and config modules resolve correctly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app import app

# Vercel serverless runtime detects 'app'
__all__ = ["app"]
