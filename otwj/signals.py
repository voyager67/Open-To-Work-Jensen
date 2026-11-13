"""Transparent source and topic labels; deliberately no truth or rumor scoring."""

from __future__ import annotations

from urllib.parse import urlparse

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


def classify_source(url: str) -> str:
    """Classify the destination host, not the feed that discovered a link."""
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if host == "nvidia.com" or host.endswith(".nvidia.com"):
        return "Company source"
    if host == "sec.gov" or host.endswith(".sec.gov"):
        return "Regulatory filing"
    if host == "news.google.com" or host.endswith(".news.google.com"):
        return "Media / aggregator"
    return "External publisher"


def topic_tags(title: str, summary: str = "") -> list[str]:
    text = f"{title} {summary}".casefold()
    return [name for name, terms in TOPICS.items() if any(term in text for term in terms)] or ["General"]
