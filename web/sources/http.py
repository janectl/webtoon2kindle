"""Conservative HTTP utilities shared by source adapters.

Only allow HTTPS and explicitly approved hosts. No cookies, credentials,
anti-bot bypass, automated browser sessions, or redirects.
"""
import ipaddress
import socket
from urllib.parse import urlsplit

import requests

from web.config import MAX_HTML_BYTES, MAX_REMOTE_FILE_BYTES


class SourceError(ValueError):
    """A usable error that can be shown to the user."""


def validate_url(url, hosts):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port not in (None, 443) or host not in hosts):
        raise SourceError("Only HTTPS URLs from supported source hosts are allowed.")

    # Defence in depth for private-address / SSRF targets.
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SourceError(f"Unable to resolve image/page host: {host}") from exc
    if not records or any(not ipaddress.ip_address(r[4][0]).is_global for r in records):
        raise SourceError("Unsafe network destination blocked.")
    return url


def download(url, hosts, *, referer=None, limit=MAX_REMOTE_FILE_BYTES):
    validate_url(url, hosts)
    headers = {"User-Agent": "Webtoon2Kindle/2.0 (personal e-reader converter)"}
    if referer:
        headers["Referer"] = referer
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.get(url, headers=headers, timeout=(10, 30),
                             stream=True, allow_redirects=False) as response:
                if response.status_code != 200:
                    raise SourceError(
                        f"Source returned HTTP {response.status_code}; "
                        "make sure the chapter is publicly accessible."
                    )
                length = response.headers.get("Content-Length")
                if length and length.isdigit() and int(length) > limit:
                    raise SourceError("Source file exceeds the allowed download limit.")
                chunks = []
                size = 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > limit:
                        raise SourceError("Source file exceeds the allowed download limit.")
                    chunks.append(chunk)
                return b"".join(chunks)
    except requests.RequestException as exc:
        raise SourceError(f"Cannot reach the source: {type(exc).__name__}") from exc


def download_html(url, hosts):
    data = download(url, hosts, referer=url, limit=MAX_HTML_BYTES)
    return data.decode("utf-8", errors="replace")