"""
Supabase Database Client

Menyediakan singleton instance Supabase client yang dipakai
di seluruh aplikasi. Kredensial dibaca dari environment variables:

  SUPABASE_URL  → Project URL dari Supabase dashboard
  SUPABASE_KEY  → service_role key (bukan anon key) agar bisa
                  bypass Row Level Security dari sisi backend

Penggunaan:
  from app.database import get_supabase
  sb = get_supabase()
  sb.table("patients").select("*").execute()
"""

import os
from functools import lru_cache

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """
    Mengembalikan Supabase Client singleton.

    Menggunakan lru_cache agar koneksi hanya dibuat sekali
    selama lifetime aplikasi berjalan.

    Raises:
        ValueError: Jika SUPABASE_URL atau SUPABASE_KEY tidak di-set.
    """
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL dan SUPABASE_KEY harus di-set sebagai environment variables. "
            "Cek file .env atau konfigurasi Kubernetes Secret kamu."
        )

    return create_client(url, key)
