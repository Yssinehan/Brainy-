"""Knowledge-graph façade used by the central AI engine."""

from __future__ import annotations

from .kg import related_entities
from brainy.memory.store import MemoryStore


class KnowledgeGraph:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def query(self, entity: str, *, hops: int = 1) -> list[dict]:
        return related_entities(self._store, entity, hops=hops)
