import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-this-secret")
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "kopi_nusantara"),
        "charset": "utf8mb4",
    }
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "images" / "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
