"""Build a conservative user profile only from persisted memory evidence."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from brainy.memory.interest_trends import extract_keywords
from brainy.memory.store import MemoryStore


class ProfileSnapshot(BaseModel):
    interests: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    frequent_topics: list[str] = Field(default_factory=list)


class PersonalProfile:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def build(self, *, limit: int = 10) -> ProfileSnapshot:
        memories = self._store.list_memories()
        keywords: Counter = Counter()
        projects: set[str] = set()
        preferences: list[str] = []
        for memory in memories:
            keywords.update(extract_keywords(memory.content))
            project = memory.meta.get("project")
            if isinstance(project, str) and project.strip():
                projects.add(project.strip())
            if memory.kind == "fact" and memory.source == "user":
                preferences.append(memory.content)
        topics = [keyword for keyword, _count in keywords.most_common(limit)]
        return ProfileSnapshot(
            interests=topics[:limit], projects=sorted(projects)[:limit],
            preferences=preferences[:limit], frequent_topics=topics,
        )
