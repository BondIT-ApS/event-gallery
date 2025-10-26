import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")
    EVENT_CODE = os.getenv("EVENT_CODE", "flowers")
    ADMIN_CODE = os.getenv("ADMIN_CODE", "champagne")
    UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "/data/uploads")
    ARCHIVE_ROOT = os.getenv("ARCHIVE_ROOT", "/data/archives")
    ENABLE_GALLERY = os.getenv("ENABLE_GALLERY", "true").lower() == "true"
    MAX_CONTENT_MB = int(os.getenv("MAX_CONTENT_MB", "512"))
    MAX_CONTENT_LENGTH = MAX_CONTENT_MB * 1024 * 1024  # Flask limit
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    ALLOWED_EXTENSIONS = {
        # Images
        "jpg","jpeg","png","heic","heif","gif","webp",
        # Video
        "mp4","mov","hevc","mkv","webm","avi"
    }

    @staticmethod
    def allowed(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS