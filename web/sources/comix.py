"""Best-effort Comix adapter for chapter pages with publicly embedded images.

Comix may deliver pages via JavaScript and may block third-party clients;
we intentionally do not emulate browser auth, reverse engineer signatures,
or bypass anti-bot or content controls.
"""
import json
import re
from collections import Counter

from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from web.sources.http import SourceError, download_html

PAGE_HOSTS = frozenset({"comix.to", "www.comix.to", "comix.ws", "www.comix.ws"})
IMAGE_HOSTS = frozenset({
    "static.comix.to", "static.comix.ws", "cdn.comix.to", "cdn.comix.ws",
    "img.comix.to", "img.comix.ws", "comix.to", "comix.ws",
})



def _image_url(value, page_url):
    if not isinstance(value, str) or not value:
        return None

    url = urljoin(page_url, value)
    split = urlsplit(url)

    if (
        split.scheme == "https"
        and split.hostname
        and not split.username
        and not split.password
        and split.port in (None, 443)
    ):
        return url

    return None


def _nested_pages(data, depth=0):
    """Only accept explicitly named reader image arrays, never thumbnails."""
    if depth > 12:
        return []
    if isinstance(data, dict):
        for key in ("pages", "chapterImages", "chapter_images", "pageImages"):
            value = data.get(key)
            if isinstance(value, list):
                found = []
                for item in value:
                    if isinstance(item, str):
                        found.append(item)
                    elif isinstance(item, dict):
                        src = item.get("url") or item.get("src") or item.get("image")
                        if isinstance(src, str):
                            found.append(src)
                if found:
                    return found
        # "images" is only recognized if a list of page records, not all site images.
        value = data.get("images")
        if isinstance(value, list) and value and all(
            isinstance(v, dict) and any(k in v for k in ("url", "src")) for v in value
        ):
            return [v.get("url") or v.get("src") for v in value]
        for value in data.values():
            result = _nested_pages(value, depth + 1)
            if result:
                return result
    elif isinstance(data, list):
        for value in data[:100]:
            result = _nested_pages(value, depth + 1)
            if result:
                return result
    return []


def parse_comix(html, url):
    soup = BeautifulSoup(html, "html.parser")
    image_urls = []

    # Prefer images in a chapter reader; never collect generic site thumbnails.
    for element in soup.select("#reader, #chapter-reader, .chapter-reader, "
                               ".reader-images, .reading-content, [data-reader]"):
        for img in element.select("img"):
            raw = img.get("data-src") or img.get("data-url") or img.get("src")
            result = _image_url(raw, url)
            if result:
                image_urls.append(result)
        if image_urls:
            break

    if not image_urls:
        for script in soup.select('script[type="application/json"], script#__NEXT_DATA__'):
            try:
                data = json.loads(script.string or script.get_text())
            except (ValueError, TypeError):
                continue
            raw_images = _nested_pages(data)
            if raw_images:
                image_urls = [_image_url(image, url) for image in raw_images]
                image_urls = [image for image in image_urls if image]
                if image_urls:
                    break

    image_urls = list(dict.fromkeys(image_urls))
    if not image_urls:
        raise SourceError(
            "Comix chapter images are not available in the public HTML. "
            "This site's JavaScript reader may restrict automated downloads. "
            "You can still upload chapter images or an authorized CBZ file."
        )

    title = soup.select_one('meta[property="og:title"]')
    title = (title.get("content") if title else None) or (
        soup.title.get_text(" ", strip=True) if soup.title else ""
    )
    segments = [part for part in urlsplit(url).path.split("/") if part]
    series = (title.split(" - ")[0].split(" | ")[0].strip() if title else "")
    if not series or series.lower() in {"comix", "comix - read comics online for free"}:
        series = re.sub(r"^[a-z0-9]+-", "", segments[1]).replace("-", " ").title()
    chapter_id = segments[2]
    match = re.search(r"chapter[-_ ]*([\d.]+)", chapter_id, re.I)
    chapter = f"Chapter {match.group(1)}" if match else "Chapter " + chapter_id.split("-")[0]
    return series, chapter, image_urls

async def _browser_images_async(url):
    """Read ordinary image URLs after scrolling a publicly accessible reader.

    The reference downloader uses nodriver and `.rpage-page[data-page]` scrolling.
    We intentionally do not import its WAF handling, cookies, canvas export,
    or blob/decryption routines. This adapter returns HTTPS image URLs only.
    """
    import asyncio
    import nodriver as uc

    browser = await uc.start(headless=False)
    try:
        tab = await browser.get(url)
        for _ in range(120):
            location = await tab.evaluate("location.href")
            title = await tab.evaluate("document.title")
            if "/@waf/challenge" in str(location) or str(title).lower() == "security check":
                await asyncio.sleep(1)
                continue
            
            count = await tab.evaluate("document.querySelectorAll('.rpage-page').length")
            if count:
                break
            await asyncio.sleep(1)
        
        else:
            raise SourceError("Comix chapter reader did not become available within 120 seconds.")

        if count > 500:
            raise SourceError("Comix chapter exceeds the browser page limit.")
        for index in range(int(count)):
            await tab.evaluate("""(function(i) {
                const page = document.querySelectorAll('.rpage-page')[i];
                if (page) page.scrollIntoView({block: 'center'});
            })(%d)""" % index)
            await asyncio.sleep(0.3)

        diagnostics = await tab.evaluate("""
        JSON.stringify(
            Array.from(document.querySelectorAll('.rpage-page'))
                .slice(0, 5)
                .map((page, index) => ({
                    page: index + 1,
                    images: Array.from(page.querySelectorAll('img')).map(img => ({
                        src: img.currentSrc || img.src,
                        loaded: img.complete,
                        width: img.naturalWidth
                    })),
                    canvases: page.querySelectorAll('canvas').length,
                    blobs: page.querySelectorAll('img[src^="blob:"]').length
                }))
        )
        """)

        print("COMIX DIAGNOSTICS:", diagnostics, flush=True)

        candidates = await tab.evaluate("""JSON.stringify(
            Array.from(document.querySelectorAll('.rpage-page img'))
                .filter(img => img.complete && img.naturalWidth > 10)
                .map(img => img.currentSrc || img.getAttribute('data-src') || img.src)
        )""")

        # Debug: identify image hosts and extraction results
        raw_urls = json.loads(candidates or "[]")

        print(
            "COMIX IMAGE HOSTS:",
            dict(Counter(urlsplit(item).hostname for item in raw_urls)),
            flush=True
        )

        print("COMIX IMAGE COUNT:", len(raw_urls), flush=True)

        accepted_urls = list(dict.fromkeys(filter(None, (
            _image_url(item, url) for item in raw_urls
        ))))

        print("COMIX ACCEPTED IMAGES:", len(accepted_urls), flush=True)

        return accepted_urls
    
    finally:
        #input("Press Enter to close Chrome...")
        browser.stop()


def browser_images(url):
    """Open a visible local Chrome browser to scroll and inspect the reader."""
    import asyncio
    import os
    from web.sources.http import validate_url
    validate_url(url, PAGE_HOSTS)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        raise SourceError("Visible Comix browser requires a desktop display. Run locally on Ubuntu, not in headless Docker.")
    try:
        return asyncio.run(_browser_images_async(url))
    except SourceError:
        raise
    except ImportError as exc:
        raise SourceError("Install nodriver to enable Comix browser extraction.") from exc
    except Exception as exc:
        raise SourceError(f"Comix browser extraction failed: {type(exc).__name__}") from exc


def import_comix(url):
    path = [part for part in urlsplit(url).path.split("/") if part]
    if len(path) != 3 or path[0] != "title":
        raise SourceError(
            "Paste a Comix chapter reader URL (https://comix.to/title/series/chapter), "
            "not a series listing."
        )
    from web.sources.http import validate_url
    validate_url(url, PAGE_HOSTS)
    images = browser_images(url)
    if not images:
        raise SourceError(
            "No direct HTTPS reader images were found. The reference downloader may "
            "use canvas/blob image data, which this first integration does not export."
        )
    series = path[1].replace("-", " ").title()
    match = re.search(r"chapter[-_ ]*([\d.]+)", path[2], re.I)
    chapter = f"Chapter {match.group(1)}" if match else path[2]
    
    dynamic_hosts = frozenset(
    urlsplit(image_url).hostname.lower()
    for image_url in images)

    return series, chapter, images, dynamic_hosts