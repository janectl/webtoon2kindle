"""Centralized operational limits. All sizes are in bytes."""
import os

def env_int(name, default):
    try:
        return max(1, int(os.getenv(name, default)))
    except (ValueError, TypeError):
        return default


MAX_UPLOAD_BYTES = env_int("MAX_UPLOAD_MB", 512) * 1024 * 1024
MAX_REMOTE_FILE_BYTES = 15 * 1024 * 1024
MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_PAGES = env_int("MAX_EPISODE_IMAGES", 500)
MAX_IMAGE_PIXELS = 50_000_000
MAX_CBZ_FILES = 20
MAX_ZIP_ENTRY_BYTES = 25 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 800 * 1024 * 1024