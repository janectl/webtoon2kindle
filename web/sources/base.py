"""Shared contract for a chapter resolved from a supported source."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    series: str
    episode: str
    image_urls: list[str]
    image_hosts: frozenset[str]
    referer: str