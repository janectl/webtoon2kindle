from flask import Flask, render_template, request, send_file
from web.importer import fetch_episode
from PIL import Image, ImageOps, ImageEnhance, UnidentifiedImageError
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from werkzeug.utils import secure_filename
from zipfile import ZipFile, ZIP_STORED
from web.cbz_merger import merge_cbz
from flask import request, send_file
from zipfile import BadZipFile
import re
import os
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


@app.route("/merge-cbz", methods=["POST"])
def merge_cbz_route():
    files = request.files.getlist("cbz_files")

    if len(files) < 2:
        return "Upload at least two CBZ files.", 400

    if any(
        not f.filename or not f.filename.lower().endswith(".cbz")
        for f in files
    ):
        return "Only CBZ files are supported.", 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(
                temp_dir, "Merged-Volume.cbz"
            )

            merge_cbz(files, output_path)

            # Materialize response before temporary directory closes.
            with open(output_path, "rb") as output:
                merged_bytes = output.read()

        from io import BytesIO

        return send_file(
            BytesIO(merged_bytes),
            as_attachment=True,
            download_name="Merged-Volume.cbz",
            mimetype="application/vnd.comicbook+zip"
        )

    except (ValueError, BadZipFile) as exc:
        return f"Invalid CBZ: {exc}", 400


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8091,
        debug=False
    )