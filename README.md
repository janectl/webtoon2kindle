# 📚 Webtoon2Kindle

**A lightweight, self-hosted WEBTOON-to-Kindle converter built with Python and Flask.**

Convert WEBTOON episodes into PDF or CBZ files for offline reading on Kindle and other e-readers.


### Why I built this

It all started because I wanted to read **Dungeon Crawler Carl** on my Kindle Paperwhite using KOReader wahahah

Since WEBTOON is designed for continuous vertical scrolling, I wanted a simple way to bring that reading experience to my E Ink device.

### ✨ Features

- Import images from publicly accessible WEBTOON episode pages
- Export episodes as PDF or CBZ
- Optional grayscale and contrast enhancement for E Ink displays
- Preserve original image proportions
- Simple Flask web interface
- Self-hosted and open source
- Support for manually uploading PNG, JPG, JPEG, and WEBP images
- Kindle Paperwhite and KOReader-friendly output


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

## 📖 How to Use

### Method 1: Import from a WEBTOON URL

1. Open a WEBTOON episode you are authorized to download.
2. Copy its episode viewer URL.
3. Open the Webtoon2Kindle web interface.
4. Paste the URL into the URL input field.
5. Select your preferred output format: **PDF** or **CBZ**.
6. Enable grayscale if you want to optimize the images for E Ink displays.
7. Click **Convert**.
8. Wait for the episode images to be processed.
9. Download the generated file.

An example of a supported episode URL structure:

```text
https://www.webtoons.com/en/genre/series/episode/viewer?title_no=1234&episode_no=1
```

Actual episode availability depends on the source page and its access restrictions.

### Method 2: Upload images manually

You can also convert your own image collection.

1. Select the images you want to convert.
2. Upload them through the web interface.
3. Choose PDF or CBZ.
4. Configure grayscale if desired.
5. Click **Convert**.
6. Download the generated file.

Supported input formats:

- PNG
- JPG
- JPEG
- WEBP




## ⚠️ Disclaimer

Webtoon2Kindle is an independent, unofficial project and is not affiliated with, endorsed by, or sponsored by WEBTOON or the creators and publishers of Dungeon Crawler Carl.

This project was developed for personal experimentation with e-reader compatibility and content that users are authorized to download and convert.

Users are responsible for complying with applicable copyright laws and the terms of service of content providers.

All rights to WEBTOON content, artwork, stories, and characters remain with their respective owners. The project's open-source license applies only to the software, not to third-party content.

## 📄 License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.