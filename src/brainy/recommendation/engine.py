"""Evidence-backed recommendations; no recommendation is emitted without a signal."""

from __future__ import annotations

from pydantic import BaseModel

from brainy.memory.interest_trends import detect_interest_trends_in_store
from brainy.memory.store import MemoryStore
from brainy.profile import PersonalProfile


class Recommendation(BaseModel):
    topic: str
    rationale: str


class RecommendationEngine:
    def __init__(self, store: MemoryStore, profile: PersonalProfile | None = None) -> None:
        self._store = store
        self._profile = profile or PersonalProfile(store)

    def generate(self, *, limit: int = 5) -> list[Recommendation]:
        trends = detect_interest_trends_in_store(self._store, k=limit)
        recommendations = [
            Recommendation(topic=trend.keyword, rationale=f"Recent memory mentions '{trend.keyword}' {trend.recent_count} times, up {trend.delta} from the previous period.")
            for trend in trends if trend.delta > 0
        ]
        if recommendations:
            return recommendations[:limit]
        profile = self._profile.build(limit=limit)
        return [
            Recommendation(topic=topic, rationale=f"'{topic}' is one of your most frequent topics in persisted memory.")
            for topic in profile.frequent_topics[:limit]
        ]
