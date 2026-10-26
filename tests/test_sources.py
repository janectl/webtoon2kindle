import pytest
from web.sources import resolve_source
from web.sources.comix import parse_comix
from web.sources.http import SourceError
from web.sources.webtoon import parse_webtoon

def test_webtoon_parser():
    html = '''<html><title>Episode 8 | Dungeon Crawler Carl</title><div id="_imageList">
        <img data-url="https://webtoon-phinf.pstatic.net/a.jpg">
        <img data-url="https://webtoon-phinf.pstatic.net/b.jpg">
        <img data-url="https://webtoon-phinf.pstatic.net/b.jpg">
        </div></html>'''
    series, ep, urls = parse_webtoon(html, "https://www.webtoons.com/en/fantasy/dungeon-crawler-carl/episode-8/viewer?episode_no=8")
    assert series == "Dungeon Crawler Carl"
    assert ep == "Episode 8"
    assert len(urls) == 2


def test_comix_parser_public_reader():
    html = '''<html><title>My Comic - Comix</title><div class="chapter-reader">
    <img data-src="https://static.comix.to/img/001.jpg">
    <img data-src="https://static.comix.to/img/002.jpg"></div></html>'''
    series, chapter, pages = parse_comix(
        html, "https://comix.to/title/abc-my-comic/8295088-chapter-42")
    assert (series, chapter) == ("My Comic", "Chapter 42")
    assert len(pages) == 2


def test_comix_embedded_json_parser():
    html = '''<script id="__NEXT_DATA__" type="application/json">{
        "props":{"chapter":{"pages":[{"url":"https://static.comix.to/i/1.jpg"},
        {"url":"https://static.comix.to/i/2.jpg"}]}}
        }</script>'''
    _, chapter, images = parse_comix(html, "https://comix.to/title/abc/8295088-chapter-1")
    assert chapter == "Chapter 1"
    assert len(images) == 2


def test_comix_dynamic_page_is_explicit():
    with pytest.raises(SourceError, match="not available in the public HTML"):
        parse_comix("<main><img src='/cover.jpg'></main>",
                    "https://comix.to/title/abc/8295088-chapter-1")


def test_comix_title_url_not_accepted(monkeypatch):
    with pytest.raises(SourceError, match="chapter reader URL"):
        resolve_source("https://comix.to/title/abc")


