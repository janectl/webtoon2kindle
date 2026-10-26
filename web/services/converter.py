"""Incremental conversion: only one decoded image is held at a time."""
import re
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_STORED

from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from web.services.cbz_merger import natural_key
from web.config import MAX_IMAGE_PIXELS, MAX_PAGES, MAX_ZIP_ENTRY_BYTES
from web.sources.http import SourceError, download

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def safe_filename(value):
    return (re.sub(r"\s+", " ", re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "", value))
            .strip(" .")[:150] or "kindle_comic")


def uploaded_pages(files):
    """Stream individual uploaded images in natural filename order."""
    files = sorted(files, key=lambda f: natural_key(f.filename))
    if not 1 <= len(files) <= MAX_PAGES:
        raise ValueError(f"Upload between 1 and {MAX_PAGES} images.")
    for upload in files:
        if PurePosixPath(upload.filename).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Accepted image types: JPG, PNG and WEBP.")
        upload.stream.seek(0)
        raw = upload.stream.read(MAX_ZIP_ENTRY_BYTES + 1)
        if len(raw) > MAX_ZIP_ENTRY_BYTES:
            raise ValueError(f"Uploaded image too large: {upload.filename}")
        yield raw


def cbz_pages(file):
    """Read uploaded CBZ one entry at a time with basic zip-bomb limits."""
    from web.services.cbz_merger import list_images
    file.stream.seek(0)
    with ZipFile(file.stream) as archive:
        items = list_images(archive)
        if not 1 <= len(items) <= MAX_PAGES:
            raise ValueError(f"CBZ must contain between 1 and {MAX_PAGES} images.")
        for item in items:
            if item.file_size > MAX_ZIP_ENTRY_BYTES:
                raise ValueError("A CBZ image exceeds the per-page size limit.")
            with archive.open(item) as image:
                raw = image.read(MAX_ZIP_ENTRY_BYTES + 1)
                if len(raw) > MAX_ZIP_ENTRY_BYTES:
                    raise ValueError("A CBZ image exceeds the per-page size limit.")
                yield raw


def remote_pages(chapter):
    for url in chapter.image_urls:
        yield download(url, chapter.image_hosts, referer=chapter.referer)


def process_image(raw, *, grayscale, contrast, max_width):
    try:
        with Image.open(BytesIO(raw)) as original:
            original.load()
            if original.width * original.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image exceeds the safe pixel limit.")
            image = ImageOps.exif_transpose(original).convert("RGB")
        if max_width and image.width > max_width:
            height = max(1, round(image.height * max_width / image.width))
            resized = image.resize((max_width, height), Image.Resampling.LANCZOS)
            image.close()
            image = resized
        if grayscale:
            gray = ImageOps.grayscale(image)
            adjusted = ImageEnhance.Contrast(gray).enhance(contrast)
            image.close()
            gray.close()
            image = adjusted.convert("RGB")
            adjusted.close()
        return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("A page is not a valid or supported image.") from exc


def convert_stream(raw_pages, output_path, output_format, *, grayscale=True,
                   contrast=1.15, max_width=0):
    """Write to disk as pages arrive, so 100+ pages do not accumulate in RAM."""
    count = 0
    if output_format == "cbz":
        with ZipFile(output_path, "w", compression=ZIP_STORED, allowZip64=True) as archive:
            for raw in raw_pages:
                count += 1
                if count > MAX_PAGES:
                    raise ValueError("Chapter exceeds the page limit.")
                image = process_image(raw, grayscale=grayscale, contrast=contrast,
                                      max_width=max_width)
                try:
                    data = BytesIO()
                    image.save(data, "JPEG", quality=83, optimize=True)
                    archive.writestr(f"{count:05d}.jpg", data.getvalue())
                    data.close()
                finally:
                    image.close()
    else:
        pdf = canvas.Canvas(output_path, pageCompression=1)
        try:
            for raw in raw_pages:
                count += 1
                if count > MAX_PAGES:
                    raise ValueError("Chapter exceeds the page limit.")
                image = process_image(raw, grayscale=grayscale, contrast=contrast,
                                      max_width=max_width)
                try:
                    pdf.setPageSize(image.size)
                    pdf.drawImage(ImageReader(image), 0, 0, width=image.width,
                                  height=image.height)
                    pdf.showPage()
                finally:
                    image.close()
        finally:
            pdf.save()
    if count == 0:
        raise ValueError("No images to convert.")
    return count