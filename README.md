# Webtoon2Kindle MVP

Self-hosted Flask app to convert authorized local PNG/JPEG/WEBP comic images into Kindle Paperwhite 6.8-inch (1236 × 1648) PDF or CBZ files.

## Install (Linux)

```bash
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8091 and upload your comic images in reading order. Choose CBZ for KOReader or PDF. Transfer the resulting file to your Kindle over USB.

## Current limitations

- Upload images only; no automatic scraping of Webtoon or DRM/access-control bypass.
- Fixed 6.8-inch Paperwhite resolution; other device presets can be added.
- Horizontal slicing does not detect panel or speech bubble boundaries.
- Image order follows browser multipart selection order; upload in reading order.
- Max 30 source images, 100 MB request, 100 million pixels per image, and 300 output pages.
- Runs on loopback only; do not expose the development server to the internet.

## Test

```bash
pip install pytest
pytest -q
```
