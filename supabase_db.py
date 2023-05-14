
import os
from supabase import create_client, Client
from datetime import datetime

from pathlib import Path
from dotenv import load_dotenv


# Initialising credentials 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)


def convertSupabaseDatetime(supabase_datetime):
    return datetime(
        int(supabase_datetime[0:4]), int(supabase_datetime[5:7]), int(supabase_datetime[8:10]), 
        int(supabase_datetime[11:13])+8, int(supabase_datetime[14:16]), 0, 0
    )