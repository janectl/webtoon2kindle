# 📚 Webtoon2Kindle

Convert WEBTOON and Comix chapters into **PDF or CBZ** files for offline reading on Kindle and other e-readers.

## 💡 Why I Built This

It started because I wanted to read **Dungeon Crawler Carl** on my Kindle Paperwhite using KOReader, wahahaha

Since webtoons are designed for vertical scrolling, I wanted a simple way to enjoy them on an E Ink device.

## 🐳 Installation

**Prerequisites:** Docker Engine, Docker Compose v2, and Git.

```bash
git clone https://github.com/janectl/webtoon2kindle.git
cd webtoon2kindle
docker compose up -d --build
```

Open **http://127.0.0.1:8091** in your browser.

> **Note:** WEBTOON conversion is supported in Docker. Comix currently requires a visible Chrome browser and should be run locally on Ubuntu until headless container support is implemented.

## 🛠️ Development

For local development on Ubuntu:

```bash
git clone https://github.com/janectl/webtoon2kindle.git
cd webtoon2kindle

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m flask --app web.app run --host 127.0.0.1 --port 8091
```

## 🚀 Development & Contributions

New features, improvements, and bug fixes are tracked through:

- [GitHub Issues](https://github.com/janectl/webtoon2kindle/issues)
- [Webtoon2Kindle Development Board](https://github.com/users/janectl/projects/3)
- [Contributing Guidelines](CONTRIBUTING.md)

Contributions and suggestions are welcome!

## ⚠️ Disclaimer

Webtoon2Kindle is an independent, unofficial project and is not affiliated with WEBTOON, Comix, or any content creators or publishers.

Use this software only with content you are authorized to download and convert. Users are responsible for complying with applicable copyright laws and content providers' terms of service.

## 📄 License

Licensed under the **MIT License**. See [LICENSE](LICENSE).