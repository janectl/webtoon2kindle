"""WEBTOON HTML episode adapter. No image buffering here."""
import re
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from web.sources.http import SourceError, download_html

PAGE_HOSTS = frozenset({"webtoons.com", "www.webtoons.com"})
IMAGE_HOSTS = frozenset({"webtoon-phinf.pstatic.net"})


def parse_webtoon(html, url):
    soup = BeautifulSoup(html, "html.parser")
    viewer = soup.select_one("#_imageList")
    if not viewer:
        raise SourceError("WEBTOON reader images were not present in the public page.")
    images = []
    seen = set()
    for tag in viewer.select("img"):
        src = tag.get("data-url") or tag.get("data-src") or tag.get("src")
        if not src:
            continue
        src = urljoin(url, src)
        if (urlsplit(src).hostname or "").lower() not in IMAGE_HOSTS:
            continue
        if src not in seen:
            seen.add(src)
            images.append(src)
    if not images:
        raise SourceError("No accessible WEBTOON image URLs found.")

    def sel_text(selector):
        node = soup.select_one(selector)
        return node.get_text(" ", strip=True) if node else ""

    series = sel_text(".subj_info .subj, .subj_info h1, .detail_header .subj")
    episode = sel_text(".subj_episode, .episode_cont .subj, .viewer_top .subj")
    title = sel_text("title")
    parts = re.split(r"\s*[|–]\s*", title)
    if len(parts) > 1:
        episode = episode or parts[0]
        series = series or parts[1]
    segments = [p for p in urlsplit(url).path.split("/") if p]
    series = series or (segments[2].replace("-", " ").title() if len(segments) > 2 else "Webtoon")
    num = parse_qs(urlsplit(url).query).get("episode_no", [""])[0]
    episode = episode or (f"Episode {num}" if num else "Episode")
    return series, episode, images


def import_webtoon(url):
    if "/viewer" not in urlsplit(url).path:
        raise SourceError("Paste a WEBTOON episode viewer link, not a series page.")
    return (*parse_webtoon(download_html(url, PAGE_HOSTS), url), IMAGE_HOSTS)