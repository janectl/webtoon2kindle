"""Site-specific adapters; the converter never needs to know the website."""
from urllib.parse import urlsplit

from web.config import MAX_PAGES
from web.sources.base import Chapter
from web.sources.comix import PAGE_HOSTS as COMIX_HOSTS, import_comix
from web.sources.http import SourceError
from web.sources.webtoon import PAGE_HOSTS as WEBTOON_HOSTS, import_webtoon


def resolve_source(url):
    host = (urlsplit(url).hostname or "").lower()
    if host in WEBTOON_HOSTS:
        series, episode, images, image_hosts = import_webtoon(url)
    elif host in COMIX_HOSTS:
        series, episode, images, image_hosts = import_comix(url)
    else:
        raise SourceError("Unsupported source. Use a WEBTOON or Comix chapter URL.")
    if not 1 <= len(images) <= MAX_PAGES:
        raise SourceError(f"Chapters must have between 1 and {MAX_PAGES} pages.")
    return Chapter(series, episode, images, image_hosts, url)