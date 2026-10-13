"""Polite breadth-first crawler for documentation that lives under a single URL prefix."""

import time
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit

import requests

USER_AGENT = "seo-rag-assistant/0.1 (educational documentation crawler)"
SKIP_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".zip", ".json", ".xml", ".txt")


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status: int
    html: str | None
    fetched_at: datetime


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and (href := dict(attrs).get("href")):
            self.hrefs.append(href)


def normalize_url(url: str) -> str:
    """Drop fragment, query string and trailing slash so each page has one canonical URL."""
    url, _ = urldefrag(url)
    scheme, netloc, path, _, _ = urlsplit(url)
    return urlunsplit((scheme.lower(), netloc.lower(), path.rstrip("/") or "/", "", ""))


def in_scope(url: str, prefix: str) -> bool:
    return (url == prefix or url.startswith(prefix + "/")) and not url.lower().endswith(
        SKIP_EXTENSIONS
    )


def extract_links(html: str, base_url: str, prefix: str) -> set[str]:
    parser = _LinkParser()
    parser.feed(html)
    links = {normalize_url(urljoin(base_url, href)) for href in parser.hrefs}
    return {link for link in links if in_scope(link, prefix)}


def crawl(
    start_url: str,
    prefix: str,
    max_pages: int = 500,
    delay_seconds: float = 1.0,
    session: requests.Session | None = None,
) -> Iterator[FetchedPage]:
    """Yield pages reachable from start_url without leaving prefix, at most one request per delay."""
    session = session or requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    prefix = normalize_url(prefix)
    start = normalize_url(start_url)
    queue, seen = deque([start]), {start}

    fetched = 0
    while queue and fetched < max_pages:
        url = queue.popleft()
        if fetched:
            time.sleep(delay_seconds)
        fetched += 1
        fetched_at = datetime.now(UTC)

        try:
            response = session.get(url, timeout=30)
        except requests.RequestException:
            yield FetchedPage(url, 0, None, fetched_at)
            continue

        is_html = response.ok and "text/html" in response.headers.get("content-type", "")
        html = response.text if is_html else None
        yield FetchedPage(url, response.status_code, html, fetched_at)

        if html:
            for link in sorted(extract_links(html, response.url, prefix) - seen):
                seen.add(link)
                queue.append(link)
