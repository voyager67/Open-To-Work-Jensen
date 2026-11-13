"""Transparent source and topic labels; deliberately no truth or rumor scoring."""

from __future__ import annotations

from urllib.parse import urlparse


OFFICIAL_HOSTS = {"nvidianews.nvidia.com", "investor.nvidia.com"}
TOPICS = {
    "Leadership": (
        "ceo", "chief executive", "succession", "successor", "interim", "board",
        "resign", "resignation", "chair", "leadership",
    ),
    "CUDA / product": (
        "cuda", "gpu", "kernel", "software", "developer", "platform", "roadmap",
        "compiler", "driver",
    ),
    "Markets": ("stock", "shares", "market", "earnings", "revenue", "nvda", "trading"),
}


def classify_source(url: str, feed_kind: str = "aggregated") -> str:
    """Classify by the linked publisher host, not by a headline's wording."""
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if host in OFFICIAL_HOSTS:
        return "Company source"
    if host == "sec.gov" or host.endswith(".sec.gov"):
        return "Regulatory filing"
    if feed_kind == "aggregated" or host == "news.google.com":
        return "Media / aggregator"
    return "External publisher"


def topic_tags(title: str, summary: str = "") -> list[str]:
    text = f"{title} {summary}".casefold()
    return [name for name, terms in TOPICS.items() if any(term in text for term in terms)] or ["General"]
