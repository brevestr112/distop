
import os
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
load_dotenv(os.path.join(BASE, ".env"))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "admin")
    PORT = int(os.environ.get("PORT", 8000))
    DB_PATH = os.path.join(DATA, "distop.db")
    UPLOAD_DIR = os.path.join(DATA, "uploads")
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("HTTPS") == "1"

    os.makedirs(DATA, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)