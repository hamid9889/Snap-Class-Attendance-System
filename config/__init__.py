"""
Configuration package for SnapClass.
Manages environment variables, Supabase connection, and application settings.
"""
from config.settings import supabase, SUPABASE_URL, SUPABASE_KEY

__all__ = ["supabase", "SUPABASE_URL", "SUPABASE_KEY"]
