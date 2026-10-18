"""Import publicly accessible WEBTOON episode images and metadata."""

from urllib.parse import urlparse, urljoin, parse_qs
from io import BytesIO
import ipaddress
import socket
import re

import requests
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError


# Configuration
MAX_BYTES = 15 * 1024 * 1024
MAX_EPISODE_IMAGES = 500

EPISODE_HOSTS = {
    "www.webtoons.com",
    "webtoons.com",
}

IMAGE_HOSTS = {
    "webtoon-phinf.pstatic.net",
}


def safe_url(url, allowed_hosts):
    """Validate HTTPS URLs and approved hosts."""

    parsed = urlparse(url)

    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(
            "Only HTTPS URLs on approved hosts are supported."
        )

    host = (parsed.hostname or "").lower()

    if host not in allowed_hosts:
        raise ValueError(f"Unsupported host: {host}")

    # Reject private and non-global IP addresses.
    try:
        addresses = socket.getaddrinfo(
            host,
            443,
            type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise ValueError(
            f"Could not resolve host: {host}"
        ) from exc

    for item in addresses:
        address = ipaddress.ip_address(item[4][0])

        if not address.is_global:
            raise ValueError(
                "Unsafe network destination."
            )

    return url


def get(url, hosts, session):
    """Download a remote file with a size limit."""

    safe_url(url, hosts)

    try:
        with session.get(
            url,
            timeout=(10, 30),
            allow_redirects=False,
            stream=True,
        ) as response:

            if response.status_code != 200:
                raise ValueError(
                    f"Remote server returned HTTP "
                    f"{response.status_code}: {url}"
                )

            size = 0
            data = BytesIO()

            for chunk in response.iter_content(65536):
                size += len(chunk)

                if size > MAX_BYTES:
                    raise ValueError(
                        "Remote file exceeds 15 MB."
                    )

                data.write(chunk)

            return data.getvalue()

    except requests.RequestException as exc:
        raise ValueError(
            f"Failed to download remote content: {exc}"
        ) from exc


def get_episode_metadata(soup, url=""):
    """Extract series and episode titles from WEBTOON HTML."""

    def clean(value):
        return re.sub(
            r"\s+", " ", value or ""
        ).strip()

    def get_meta(*selectors):
        for selector in selectors:
            tag = soup.select_one(selector)

            if tag:
                content = clean(tag.get("content", ""))

                if content:
                    return content

        return ""

    series = ""
    episode = ""

    # 1. Try WEBTOON HTML selectors.
    series_tag = soup.select_one(
        ".subj_info .subj, "
        ".subj_info h1, "
        ".detail_header .subj, "
        ".info .subj"
    )

    episode_tag = soup.select_one(
        ".subj_episode, "
        ".episode_cont .subj, "
        ".viewer_top .subj, "
        ".subj_info h2"
    )

    if series_tag:
        series = clean(
            series_tag.get_text(" ", strip=True)
        )

    if episode_tag:
        episode = clean(
            episode_tag.get_text(" ", strip=True)
        )

    # 2. Try Open Graph metadata.
    if not series:
        series = get_meta(
            'meta[property="og:site_name"]'
        )

        if series.lower() in {
            "webtoon",
            "webtoons"
        }:
            series = ""

    # 3. Try the HTML title.
    title_tag = soup.find("title")

    page_title = clean(
        title_tag.get_text(" ", strip=True)
        if title_tag else ""
    )

    if page_title and (not series or not episode):
        # Example:
        # Episode 1 | Dungeon Crawler Carl
        parts = re.split(
            r"\s*[|–]\s*",
            page_title
        )

        if len(parts) >= 2:
            episode = episode or parts[0]
            series = series or parts[1]

    # 4. Use episode number from the URL.
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    episode_no = params.get(
        "episode_no", [""]
    )[0]

    if not episode:
        episode = (
            f"Episode {episode_no}"
            if episode_no
            else "Episode"
        )

    # 5. Use the series slug as a fallback.
    if not series:
        # Example:
        # /en/fantasy/dungeon-crawler-carl/episode-1/viewer
        segments = [
            segment
            for segment in parsed.path.split("/")
            if segment
        ]

        if len(segments) >= 3:
            series = (
                segments[2]
                .replace("-", " ")
                .title()
            )
        else:
            series = "Webtoon"

    return {
        "series": series,
        "episode": episode,
    }


def fetch_episode(url):
    """Fetch episode images and extracted metadata."""

    safe_url(url, EPISODE_HOSTS)

    if "/viewer" not in urlparse(url).path:
        raise ValueError(
            "Paste a valid WEBTOON episode viewer URL."
        )

    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0 Webtoon2Kindle/1.0",
        "Referer": url,
    })

    try:
        # Download the episode HTML.
        html = get(url, EPISODE_HOSTS, session)

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # Extract filename metadata.
        metadata = get_episode_metadata(
            soup,
            url
        )

        print(
            f"[Webtoon2Kindle] Series: "
            f"{metadata['series']}",
            flush=True,
        )

        print(
            f"[Webtoon2Kindle] Episode: "
            f"{metadata['episode']}",
            flush=True,
        )

        # Locate episode images.
        viewer = soup.select_one("#_imageList")

        if viewer is None:
            raise ValueError(
                "Episode image container not found."
            )

        image_urls = []

        for tag in viewer.select("img"):
            src = (
                tag.get("data-url")
                or tag.get("data-src")
                or tag.get("src")
            )

            if not src:
                continue

            src = urljoin(url, src)

            host = (
                urlparse(src).hostname or ""
            ).lower()

            if host not in IMAGE_HOSTS:
                raise ValueError(
                    f"Unexpected episode image host: {host}"
                )

            image_urls.append(src)

        if not image_urls:
            raise ValueError(
                "No episode images found."
            )

        if len(image_urls) > MAX_EPISODE_IMAGES:
            raise ValueError(
                f"Episode contains {len(image_urls)} "
                f"images. Maximum allowed: "
                f"{MAX_EPISODE_IMAGES}."
            )

        print(
            f"[Webtoon2Kindle] Found "
            f"{len(image_urls)} images.",
            flush=True,
        )

        # Download images in reading order.
        images = []

        for index, src in enumerate(
            image_urls,
            start=1
        ):
            print(
                f"[Webtoon2Kindle] Downloading "
                f"{index}/{len(image_urls)}",
                flush=True,
            )

            data = get(
                src,
                IMAGE_HOSTS,
                session
            )

            try:
                with Image.open(
                    BytesIO(data)
                ) as img:
                    img.verify()

                with Image.open(
                    BytesIO(data)
                ) as img:
                    images.append(
                        img.copy()
                    )

            except (
                UnidentifiedImageError,
                OSError,
                Image.DecompressionBombError,
            ) as exc:
                raise ValueError(
                    f"Could not decode image {index}."
                ) from exc

        print(
            "[Webtoon2Kindle] "
            "All images downloaded.",
            flush=True,
        )

        return images, metadata

    finally:
        session.close()