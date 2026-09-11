"""Application service for long-term memory operations.

This façade keeps orchestration code independent of the SQLite/Chroma details while
preserving the existing storage and retrieval implementations.
"""

from __future__ import annotations

from brainy.router import ModelRouter

from .ingest import IngestResult, ingest_text
from .retrieve import RetrievedChunk, semantic_search
from .store import MemoryStore
from .types import MemoryRecord
from .vectors import VectorStore


class MemoryManager:
    def __init__(self, store: MemoryStore, vectors: VectorStore, router: ModelRouter) -> None:
        self._store = store
        self._vectors = vectors
        self._router = router

    def remember(self, content: str, *, importance: float = 0.7, source: str = "user") -> MemoryRecord:
        record = MemoryRecord(kind="fact", content=content, source=source, importance=importance)
        self._store.add_memory(record)
        self._store.log("user", "remember", {"memory_id": record.id, "source": source})
        return record

    def retrieve(self, query: str, *, k: int | None = None) -> list[RetrievedChunk]:
        return semantic_search(self._store, self._vectors, self._router, query, k=k)

    def ingest(self, text: str, *, doc_id: str, source: str = "user") -> IngestResult:
        return ingest_text(self._store, self._vectors, self._router, text=text, doc_id=doc_id, source=source)

    def stats(self) -> dict:
        return self._store.stats()
