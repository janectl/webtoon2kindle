# Webtoon2Kindle

Local Flask converter for Kindle Paperwhite 4 (6-inch, 1072 x 1448). Supports PDF and CBZ, URL-based import of accessible WEBTOON episode images, or manual image upload. No authentication, DRM bypass, or access-control circumvention. Use only with content you are permitted to download and convert.

## Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8091 and paste a WEBTOON episode URL or upload images. Select PDF or CBZ. Files download to your browser.

## Limitations

- URL import relies on the episode's publicly available HTML and may stop working when WEBTOON changes markup or blocks requests.
- This is a local-only, synchronous MVP; episodes can take a while to process.
- Page boundaries are fixed, not panel-aware.
- Importer allows only WEBTOON viewer pages and known static-image hosts, with basic SSRF protections. Do not expose the Flask development server to the internet.
