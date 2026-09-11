"""Small deterministic temporal parser for retrieval constraints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from brainy.memory.retrieve import RetrievedChunk


def filter_recent(results: list[RetrievedChunk], query: str, *, now: datetime | None = None) -> list[RetrievedChunk]:
    """Apply supported relative-time constraints; leave queries without one untouched."""
    text = query.lower()
    now = now or datetime.now(timezone.utc)
    if "today" in text:
        cutoff = now - timedelta(days=1)
    elif "yesterday" in text:
        start, end = now - timedelta(days=2), now - timedelta(days=1)
        return [result for result in results if start <= _timestamp(result) < end]
    elif "last week" in text:
        cutoff = now - timedelta(days=7)
    elif "last month" in text:
        cutoff = now - timedelta(days=31)
    else:
        return results
    return [result for result in results if _timestamp(result) >= cutoff]


def _timestamp(result: RetrievedChunk) -> datetime:
    value = result.created_at or ""
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
