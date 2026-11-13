"""Polite, attribution-preserving RSS/Atom ingestion for public sources."""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urlparse


USER_AGENT = "open-to-work-jensen/1.0 (+https://github.com/voyager67/Open-To-Work-Jensen)"
MAX_FEED_BYTES = 1_000_000
MAX_SUMMARY_CHARS = 280
REQUEST_TIMEOUT_SECONDS = 7
REQUEST_GAP_SECONDS = 1.25

# NVIDIA documents its RSS feeds on its newsroom and investor-relations sites.
# The Google News feed is discovery-only: each publisher link remains visible.
FEEDS: list[dict[str, str]] = [
    {
        "name": "NVIDIA Newsroom — press releases",
        "url": "https://nvidianews.nvidia.com/cats/press_release.xml",
        "kind": "official",
    },
    {
        "name": "NVIDIA Investor Relations — SEC filings",
        "url": "https://investor.nvidia.com/rss/SECFiling.aspx?Exchange=CIK&Symbol=0001045810",
        "kind": "regulatory",
    },
    {
        "name": "Google News — NVIDIA leadership coverage",
        "url": "https://news.google.com/rss/search?q=NVIDIA+Jensen+Huang+CEO+succession&hl=en-US&gl=US&ceid=US:en",
        "kind": "aggregated",
    },
]


@dataclass(frozen=True)
class Article:
    """Minimal metadata for one source item; article text is not republished."""

    title: str
    url: str
    published: datetime | None
    publisher: str
    feed_name: str
    feed_kind: str
    summary: str = ""


class _VisibleText(HTMLParser):
    """Extract visible text from feed descriptions without retaining markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth and data.strip():
            self.parts.append(data.strip())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def _text(parent: ET.Element, names: Iterable[str]) -> str:
    wanted = {name.casefold() for name in names}
    for node in parent.iter():
        if node is parent:
            continue
        if _local_name(node.tag) in wanted and node.text:
            return node.text.strip()
    return ""


def _clean_summary(value: str) -> str:
    parser = _VisibleText()
    try:
        parser.feed(value)
        parser.close()
        text = " ".join(parser.parts)
    except Exception:
        # A malformed description should not make the rest of a feed unusable.
        text = value
    text = re.sub(r"\s+([.,!?;:])", r"\1", " ".join(text.split()))
    return text[:MAX_SUMMARY_CHARS]


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username


def _parse_rss(root: ET.Element, feed: dict[str, str]) -> list[Article]:
    articles: list[Article] = []
    for item in (node for node in root.iter() if _local_name(node.tag) == "item"):
        title = _text(item, ["title"])
        url = _text(item, ["link"])
        date_text = _text(item, ["pubDate", "date", "published", "updated"])
        publisher = _text(item, ["source", "creator", "author"]) or feed["name"]
        summary = _clean_summary(_text(item, ["description", "encoded", "summary"]))
        if title and _valid_http_url(url):
            articles.append(
                Article(
                    title=title,
                    url=url.strip(),
                    published=_parse_date(date_text),
                    publisher=publisher,
                    feed_name=feed["name"],
                    feed_kind=feed["kind"],
                    summary=summary,
                )
            )
    return articles


def _parse_atom(root: ET.Element, feed: dict[str, str]) -> list[Article]:
    articles: list[Article] = []
    for entry in (node for node in root.iter() if _local_name(node.tag) == "entry"):
        title = _text(entry, ["title"])
        links = [node for node in entry if _local_name(node.tag) == "link"]
        link = next((node for node in links if node.attrib.get("rel", "alternate") == "alternate"), links[0] if links else None)
        url = link.attrib.get("href", "") if link is not None else ""
        date_text = _text(entry, ["published", "updated"])
        author = next((node for node in entry if _local_name(node.tag) == "author"), None)
        publisher = _text(author, ["name"]) if author is not None else feed["name"]
        summary = _clean_summary(_text(entry, ["summary", "content"]))
        if title and _valid_http_url(url):
            articles.append(
                Article(
                    title=title,
                    url=url.strip(),
                    published=_parse_date(date_text),
                    publisher=publisher or feed["name"],
                    feed_name=feed["name"],
                    feed_kind=feed["kind"],
                    summary=summary,
                )
            )
    return articles


def fetch_feed(feed: dict[str, str], timeout: int = REQUEST_TIMEOUT_SECONDS, limit: int = 30) -> list[Article]:
    """Fetch one public RSS/Atom feed, with a short timeout and bounded response size."""
    if not _valid_http_url(feed.get("url", "")):
        raise ValueError("Feed URL must be an absolute HTTP(S) URL.")

    request = urllib.request.Request(
        feed["url"],
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_FEED_BYTES + 1)
    if len(body) > MAX_FEED_BYTES:
        raise ValueError(f"Feed exceeded the {MAX_FEED_BYTES:,}-byte safety limit.")

    root = ET.fromstring(body)
    articles = _parse_rss(root, feed)
    if not articles:
        articles = _parse_atom(root, feed)
    return articles[: max(0, limit)]


def fetch_all_feeds(
    feeds: list[dict[str, str]] | None = None,
    *,
    request_gap: float = REQUEST_GAP_SECONDS,
) -> tuple[list[Article], list[str]]:
    """Fetch configured feeds; isolate failures and preserve source attribution."""
    selected_feeds = FEEDS if feeds is None else feeds
    collected: list[Article] = []
    errors: list[str] = []

    for index, feed in enumerate(selected_feeds):
        if index and request_gap > 0:
            time.sleep(request_gap)
        try:
            collected.extend(fetch_feed(feed))
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError, ValueError) as exc:
            errors.append(f"{feed['name']}: {type(exc).__name__}: {exc}")

    unique: dict[str, Article] = {}
    for article in collected:
        unique.setdefault(article.url, article)
    sorted_articles = sorted(
        unique.values(),
        key=lambda item: item.published or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return sorted_articles, errors
