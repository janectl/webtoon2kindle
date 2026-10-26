"""Flask application. Routing is deliberately kept separate from conversion."""
import os
from tempfile import TemporaryDirectory
from urllib.parse import quote
from zipfile import BadZipFile

from flask import Flask, Response, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.http import dump_options_header

from web.services.cbz_merger import episode_number, merge_cbz, sort_episodes
from web.config import MAX_CBZ_FILES, MAX_UPLOAD_BYTES
from web.services.converter import (cbz_pages, convert_stream, remote_pages, safe_filename,
                           uploaded_pages)
from web.sources import resolve_source


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_):
        return ("The upload exceeds the configured limit. For large CBZ merges, "
                "increase MAX_UPLOAD_MB and your reverse proxy's client_max_body_size.", 413)

    def download_temp(output_path, tempdir, name, mimetype):
        """Read from disk in chunks; free temporary disk space after transfer."""
        def stream():
            try:
                with open(output_path, "rb") as archive:
                    while chunk := archive.read(1024 * 1024):
                        yield chunk
            finally:
                tempdir.cleanup()

        response = Response(stream(), mimetype=mimetype)
        ascii_name = name.encode("ascii", errors="ignore").decode() or "comic.cbz"
        response.headers["Content-Disposition"] = (
            dump_options_header("attachment", {"filename": ascii_name})
            + f"; filename*=UTF-8''{quote(name)}"
        )
        response.content_length = os.path.getsize(output_path)
        return response

    @app.post("/inspect")
    def inspect_chapter():
        url = request.form.get("url", "").strip()
        if not url:
            return {"error": "Paste a chapter URL first."}, 400
        try:
            chapter = resolve_source(url)
            return {"series": chapter.series, "episode": chapter.episode,
                    "page_count": len(chapter.image_urls)}
        except (ValueError, OSError) as exc:
            return {"error": str(exc)}, 400

    @app.post("/convert")
    def convert():
        url = request.form.get("url", "").strip()
        images = [file for file in request.files.getlist("images") if file.filename]
        cbz = request.files.get("cbz")
        if cbz and not cbz.filename:
            cbz = None
        if int(bool(url)) + int(bool(images)) + int(bool(cbz)) != 1:
            return "Provide one input: chapter URL, image uploads, or a CBZ archive.", 400

        output = request.form.get("format", "cbz")
        if output not in {"pdf", "cbz"}:
            return "Invalid export format.", 400
        try:
            contrast = float(request.form.get("contrast", "1.15"))
            if not 0.5 <= contrast <= 2.0:
                raise ValueError("Contrast must be between 0.5 and 2.0.")
            max_width = int(request.form.get("max_width", "0"))
            if max_width not in (0, 1072, 1264, 1448):
                raise ValueError("Invalid image width option.")
            grayscale = request.form.get("grayscale") == "on"
            if url:
                chapter = resolve_source(url)
                raw_pages = remote_pages(chapter)
                name = safe_filename(f"{chapter.series} - {chapter.episode}")
            elif cbz:
                if not cbz.filename.lower().endswith(".cbz"):
                    raise ValueError("Only .cbz archives can be imported.")
                raw_pages = cbz_pages(cbz)
                name = safe_filename(cbz.filename.rsplit(".", 1)[0])
            else:
                raw_pages = uploaded_pages(images)
                name = safe_filename(request.form.get("name", "Comic") or "Comic")

            tempdir = TemporaryDirectory(prefix="webtoon2kindle-")
            try:
                output_path = os.path.join(tempdir.name, f"converted.{output}")
                convert_stream(raw_pages, output_path, output,
                               grayscale=grayscale, contrast=contrast,
                               max_width=max_width)
            except Exception:
                tempdir.cleanup()
                raise
            mimetype = ("application/pdf" if output == "pdf" else
                        "application/vnd.comicbook+zip")
            return download_temp(output_path, tempdir, f"{name}.{output}", mimetype)
        except (ValueError, OSError, BadZipFile) as exc:
            return str(exc), 400

    @app.post("/merge-cbz")
    def merge_cbz_route():
        files = [file for file in request.files.getlist("cbz_files") if file.filename]
        if not 2 <= len(files) <= MAX_CBZ_FILES:
            return f"Select between 2 and {MAX_CBZ_FILES} CBZ files.", 400
        if any(not file.filename.lower().endswith(".cbz") for file in files):
            return "Only CBZ files can be merged.", 400
        if request.form.get("order_mode") != "manual":
            files = sort_episodes(files)
        name = safe_filename(request.form.get("volume_name", "") or "Merged Volume")
        numbers = [episode_number(f.filename) for f in files]
        if all(number is not None for number in numbers):
            name += f" - Episodes {numbers[0]}-{numbers[-1]}"
        tempdir = TemporaryDirectory(prefix="webtoon2kindle-merge-")
        try:
            output_path = os.path.join(tempdir.name, "merged.cbz")
            merge_cbz(files, output_path)
        except (ValueError, OSError, BadZipFile) as exc:
            tempdir.cleanup()
            return f"Unable to merge CBZ files: {exc}", 400
        return download_temp(output_path, tempdir, f"{name}.cbz",
                             "application/vnd.comicbook+zip")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8091, debug=False)