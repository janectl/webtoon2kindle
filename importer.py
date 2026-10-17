"""Import publicly accessible WEBTOON episode images."""

from urllib.parse import urlparse, urljoin
from io import BytesIO
import ipaddress
import socket

import requests
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError


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

    for item in socket.getaddrinfo(
        host, 443, type=socket.SOCK_STREAM
    ):
        address = ipaddress.ip_address(item[4][0])

        if not address.is_global:
            raise ValueError("Unsafe network destination.")

    return url


def get(url, hosts, session):
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


def fetch_episode(url):
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

    html = get(url, EPISODE_HOSTS, session)

    soup = BeautifulSoup(html, "html.parser")

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
        host = (urlparse(src).hostname or "").lower()

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
            f"Episode contains {len(image_urls)} images. "
            f"Maximum allowed: {MAX_EPISODE_IMAGES}."
        )

    print(
        f"[Webtoon2Kindle] Found {len(image_urls)} images.",
        flush=True,
    )

    images = []

    for index, src in enumerate(image_urls, start=1):
        print(
            f"[Webtoon2Kindle] Downloading "
            f"{index}/{len(image_urls)}",
            flush=True,
        )

        data = get(src, IMAGE_HOSTS, session)

        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()

            with Image.open(BytesIO(data)) as img:
                images.append(img.copy())

        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
        ) as exc:
            raise ValueError(
                f"Could not decode image {index}."
            ) from exc

    print(
        "[Webtoon2Kindle] All images downloaded.",
        flush=True,
    )

    return images
