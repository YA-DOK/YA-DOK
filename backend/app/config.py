import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "medical-case-images").strip()
SIGNED_URL_SECONDS = int(os.getenv("SIGNED_URL_SECONDS", "300"))
