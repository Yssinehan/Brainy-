from datetime import datetime, timedelta, timezone

from brainy.memory.retrieve import RetrievedChunk
from brainy.rag.temporal import filter_recent


def _result(created_at: str) -> RetrievedChunk:
    return RetrievedChunk(chunk_id="chunk", doc_id="doc", text="text", source="test", similarity=1.0, importance=0.5, rank_score=1.0, created_at=created_at)


def test_last_week_filters_out_old_results():
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    recent = _result((now - timedelta(days=2)).isoformat())
    old = _result((now - timedelta(days=10)).isoformat())

    assert filter_recent([recent, old], "what happened last week?", now=now) == [recent]
