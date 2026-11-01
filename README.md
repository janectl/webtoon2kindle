# 📚 Webtoon2Kindle

**A lightweight, self-hosted WEBTOON-to-Kindle converter built with Python and Flask.**

Convert WEBTOON episodes into PDF or CBZ files for offline reading on Kindle and other e-readers.


### Why I built this

It all started because I wanted to read **Dungeon Crawler Carl** on my Kindle Paperwhite using KOReader wahahah

Since WEBTOON is designed for continuous vertical scrolling, I wanted a simple way to bring that reading experience to my E Ink device.


## 📋 Prerequisites

For the recommended Docker installation:

-   Docker Engine (or Docker Desktop)
-   Docker Compose v2 (`docker compose`)
-   Git
-   A web browser
-   An internet connection for importing WEBTOON episodes

**You do not need to install Python, pip, or create a virtual
environment on your host** when using Docker.

## 🐳 Installation with Docker Compose (Recommended)

### 1. Clone the repository

``` bash
git clone https://github.com/janectl/webtoon2kindle.git
cd webtoon2kindle
```

### 2. Build and start the container

``` bash
docker compose up -d --build
```

Docker Compose builds the application image, installs its Python
dependencies, and starts the container.

### 3. Verify the container

``` bash
docker compose ps
```

To view application logs:

``` bash
docker compose logs -f webtoon2kindle
```

### 4. Open the web interface

On the same computer running Docker, open:

**http://127.0.0.1:8091**


Webtoon2Kindle is now ready to use!


## ⚠️ Disclaimer

Webtoon2Kindle is an independent, unofficial project and is not affiliated with, endorsed by, or sponsored by WEBTOON or the creators and publishers of Dungeon Crawler Carl.

This project was developed for personal experimentation with e-reader compatibility and content that users are authorized to download and convert.

Users are responsible for complying with applicable copyright laws and the terms of service of content providers.

All rights to WEBTOON content, artwork, stories, and characters remain with their respective owners. The project's open-source license applies only to the software, not to third-party content.

## 📄 License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.