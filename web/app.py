from flask import Flask, Response, render_template, request, send_file
from web.importer import fetch_episode
from web.cbz_merger import merge_cbz, sort_episodes, episode_number

from PIL import Image, ImageOps, ImageEnhance, UnidentifiedImageError
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
from zipfile import ZipFile, ZIP_STORED, BadZipFile
from werkzeug.utils import secure_filename
from tempfile import TemporaryDirectory

import os
import re

import tempfile

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

MAX_IMAGES = 30
MAX_PIXELS = 100_000_000

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def safe_download_name(value):
    """Create a readable, filesystem-safe download filename."""

    value = re.sub(r'[\\/:*?"<>|]+', '', value)
    value = re.sub(r'\s+', ' ', value).strip(' .')

    return value[:150] or 'kindle_comic'


def convert_images(files, grayscale=True, contrast=1.15):
    pages = []

    for file in files:
        name = secure_filename(
            getattr(file, 'filename', 'episode.jpg') or 'episode.jpg'
        )

        if not isinstance(file, Image.Image):
            if not name.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.webp')
            ):
                raise ValueError('Unsupported image format.')

        try:
            img = (
                file.copy()
                if isinstance(file, Image.Image)
                else Image.open(file.stream)
            )

            if img.width * img.height > MAX_PIXELS:
                raise ValueError('Image exceeds pixel limit.')

            img = ImageOps.exif_transpose(img).convert('RGB')

            if grayscale:
                img = ImageOps.grayscale(img)
                img = ImageEnhance.Contrast(img).enhance(contrast)
                img = img.convert('RGB')

            # Preserve original image dimensions.
            # No height splitting or resizing.
            pages.append(img)

        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError
        ) as exc:
            raise ValueError(f'Invalid image: {name}') from exc

    return pages


def export_pdf(pages):
    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pageCompression=1
    )

    for page in pages:
        width, height = page.size

        pdf.setPageSize((width, height))

        pdf.drawImage(
            ImageReader(page),
            0,
            0,
            width=width,
            height=height
        )

        pdf.showPage()

    pdf.save()
    buffer.seek(0)

    return buffer


def export_cbz(pages):
    buffer = BytesIO()

    with ZipFile(buffer, 'w', ZIP_STORED) as archive:
        for i, page in enumerate(pages, 1):
            image_data = BytesIO()

            page.save(
                image_data,
                format='JPEG',
                quality=85,
                optimize=True,
                progressive=False,
                **(
                    {'subsampling': 0}
                    if page.mode == 'RGB'
                    else {}
                )
            )

            archive.writestr(
                f'{i:04d}.jpg',
                image_data.getvalue()
            )

            image_data.close()
            page.close()

    buffer.seek(0)
    return buffer

@app.get('/')
def index():
    return render_template('index.html')


@app.post('/convert')
def convert():
    files = [
        f for f in request.files.getlist('images')
        if f.filename
    ]

    url = request.form.get('url', '').strip()

    if not url and (not files or len(files) > MAX_IMAGES):
        return 'Paste a URL or upload between 1 and 30 images.', 400

    output = request.form.get('format', 'cbz')

    if output not in ('pdf', 'cbz'):
        return 'Invalid format.', 400

    try:
        # Import WEBTOON images and episode metadata.
        if url:
            source, metadata = fetch_episode(url)

            filename = safe_download_name(
                f"{metadata['series']} - {metadata['episode']}"
            )

        else:
            source = files
            filename = 'kindle_comic'

        # Convert images only once.
        pages = convert_images(
            source,
            grayscale=request.form.get('grayscale') == 'on'
        )

        # Export only once.
        if output == 'pdf':
            data = export_pdf(pages)
            mimetype = 'application/pdf'
        else:
            data = export_cbz(pages)
            mimetype = 'application/vnd.comicbook+zip'

    except (ValueError, OSError) as exc:
        return str(exc), 400

    return send_file(
        data,
        mimetype=mimetype,
        as_attachment=True,
        download_name=f'{filename}.{output}'
    )


@app.post("/merge-cbz")
def merge_cbz_route():
    files = [
        file
        for file in request.files.getlist("cbz_files")
        if file.filename
    ]

    if not 2 <= len(files) <= 20:
        return "Select between 2 and 20 CBZ files.", 400

    if any(
        not file.filename.lower().endswith(".cbz")
        for file in files
    ):
        return "Only CBZ files are supported.", 400

    # Default: sort by episode number.
    # Manual: respect the exact order sent by the browser.
    if request.form.get("order_mode") != "manual":
        files = sort_episodes(files)

    numbers = [
        episode_number(file.filename)
        for file in files
    ]

    series_name = safe_download_name(
        request.form.get("volume_name", "").strip()
    )

    if not request.form.get("volume_name", "").strip():
        series_name = "Merged-Volume"

    if all(number is not None for number in numbers):
        filename = (
            f"{series_name} - Episodes "
            f"{numbers[0]}-{numbers[-1]}.cbz"
        )
    else:
        filename = f"{series_name}.cbz"

    temp_dir = TemporaryDirectory()
    output_path = os.path.join(temp_dir.name, "merged.cbz")

    try:
        total_pages = merge_cbz(files, output_path)

        print(
            f"[Webtoon2Kindle] Merged {len(files)} episodes "
            f"into {total_pages} pages",
            flush=True,
        )

    except (ValueError, BadZipFile, OSError) as exc:
        temp_dir.cleanup()
        return f"Unable to merge CBZ files: {exc}", 400

    def stream_archive():
        try:
            with open(output_path, "rb") as archive:
                while chunk := archive.read(1024 * 1024):
                    yield chunk
        finally:
            temp_dir.cleanup()

    response = Response(
        stream_archive(),
        mimetype="application/vnd.comicbook+zip",
    )

    response.headers["Content-Disposition"] = (
        f"attachment; filename=\"{filename}\""
    )
    response.content_length = os.path.getsize(output_path)

    return response


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8091,
        debug=False
    )