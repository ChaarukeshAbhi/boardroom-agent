from supabase import create_client, Client
from utils.config import settings

# Debug (safe)
print("DB SUPABASE_URL =", settings.SUPABASE_URL)
print("DB SUPABASE_KEY =", "FOUND" if settings.SUPABASE_KEY else None)

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
    raise RuntimeError("Supabase credentials missing in database.py")

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)