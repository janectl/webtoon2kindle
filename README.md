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

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3 | Application programming language |
| Flask | Web application backend |
| Pillow | Image processing and grayscale conversion |
| Requests | Downloading episode images |
| BeautifulSoup4 | Parsing WEBTOON episode HTML |
| ReportLab | PDF generation |
| zipfile | CBZ archive generation |
| HTML/CSS | Web interface |

## 📋 Prerequisites

Before running Webtoon2Kindle, make sure you have:

- Python 3.10 or newer
- pip
- Git
- A web browser
- An internet connection for importing episodes

The instructions below are intended for Linux. The application can also run on Windows and macOS with the appropriate Python environment.

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/janectl/webtoon2kindle.git
cd Webtoon2Kindle
```


### 2. Create a Python virtual environment

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

For Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install the dependencies manually:

```bash
pip install flask pillow requests beautifulsoup4 reportlab werkzeug
```

### 4. Run the application

```bash
python3 app.py
```

The Flask development server should start on:

```text
http://127.0.0.1:8091
```

### 5. Access the web interface

Open your browser and navigate to:

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

## 📱 Reading on Kindle

Webtoon2Kindle was originally developed for the **Kindle Paperwhite 4 (6-inch display, 1072 × 1448 resolution)** using KOReader.

### Transfer the converted file

1. Connect your Kindle to your computer using a USB cable.
2. Open the Kindle storage directory.
3. Copy the generated PDF or CBZ file into your preferred folder.
4. Safely eject the Kindle.
5. Open KOReader.
6. Navigate to the file and start reading.

### Recommended settings

For the best experience on an E Ink device:

| Setting | Recommendation |
|---|---|
| Output format | CBZ |
| Grayscale | Enabled |
| Contrast | 1.15 |
| Image aspect ratio | Preserve original |
| Reader | KOReader |
| Display settings | Adjust zoom and fit-to-width as needed |

**Why CBZ?**

CBZ files are ZIP archives containing images in reading order. KOReader can open them directly, making CBZ a practical choice for image-based comics.

PDF is also supported, especially if you prefer a single document with individual image pages.

### A note about WEBTOON image segments

WEBTOON uses a continuous vertical reading format, but episodes may be delivered as multiple image segments.

Webtoon2Kindle preserves the original image proportions without introducing additional height-based splitting.

However, panels may still span multiple images because the source content is already segmented.

The application does not automatically merge all source images into one continuous image.



## ⚠️ Disclaimer

Webtoon2Kindle is an independent, unofficial project and is not affiliated with, endorsed by, or sponsored by WEBTOON or the creators and publishers of Dungeon Crawler Carl.

This project was developed for personal experimentation with e-reader compatibility and content that users are authorized to download and convert.

Users are responsible for complying with applicable copyright laws and the terms of service of content providers.

All rights to WEBTOON content, artwork, stories, and characters remain with their respective owners. The project's open-source license applies only to the software, not to third-party content.

## 📄 License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.