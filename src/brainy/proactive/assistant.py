"""Deterministic, low-noise proactive signals over stored task/project evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from brainy.memory.store import MemoryStore
from brainy.memory.time_utils import days_since


class ProactiveInsight(BaseModel):
    kind: str
    message: str
    priority: int


class ProactiveAssistant:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def inspect(self, *, inactive_after_days: float = 7.0, limit: int = 5) -> list[ProactiveInsight]:
        insights: list[ProactiveInsight] = []
        for memory in self._store.list_memories():
            project = memory.meta.get("project")
            if not isinstance(project, str) or not project:
                continue
            age = days_since(memory.last_accessed or memory.created_at)
            if age >= inactive_after_days:
                insights.append(ProactiveInsight(kind="inactive_project", message=f"You have not revisited project '{project}' for {int(age)} days.", priority=min(100, int(age))))
        insights.sort(key=lambda insight: insight.priority, reverse=True)
        return insights[:limit]
