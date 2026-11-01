"""Merge CBZ archives by copying compressed page bytes without decoding."""
import re
import shutil
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_STORED

from web.config import MAX_ZIP_ENTRY_BYTES, MAX_ZIP_TOTAL_BYTES

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def natural_key(value):
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)]


def episode_number(filename):
    match = re.search(r"(?:episode|ep|chapter|ch)[\s._-]*(\d+)", filename, re.I)
    return int(match.group(1)) if match else None


def sort_episodes(files):
    return sorted(files, key=lambda file: (
        episode_number(file.filename) is None,
        episode_number(file.filename) or 0,
        natural_key(file.filename),
    ))


def list_images(archive):
    images = [item for item in archive.infolist()
              if not item.is_dir()
              and PurePosixPath(item.filename).suffix.lower() in IMAGE_EXTENSIONS
              and "__MACOSX" not in item.filename.split("/")]
    return sorted(images, key=lambda item: natural_key(item.filename))

def merge_cbz(files, output_path):
    """Preserve bytes and reading order, with explicit size/entry limits."""
    total_pages = 0
    total_uncompressed = 0
    with ZipFile(output_path, "w", compression=ZIP_STORED, allowZip64=True) as output:
        for uploaded_file in files:
            uploaded_file.stream.seek(0)
            with ZipFile(uploaded_file.stream) as source:
                images = list_images(source)
                if not images:
                    raise ValueError(f"No images found in {uploaded_file.filename}")
                for item in images:
                    if item.file_size > MAX_ZIP_ENTRY_BYTES:
                        raise ValueError("One CBZ page exceeds the 25 MB size limit.")
                    total_uncompressed += item.file_size
                    if total_uncompressed > MAX_ZIP_TOTAL_BYTES:
                        raise ValueError("Merged CBZ exceeds the 800 MB unpacked limit.")
                    total_pages += 1
                    extension = PurePosixPath(item.filename).suffix.lower()
                    name = f"{total_pages:06d}{extension}"
                    with source.open(item) as src, output.open(name, "w") as dest:
                        shutil.copyfileobj(src, dest, length=1024 * 1024)
    return total_pages