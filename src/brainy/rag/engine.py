"""Stable application-facing façade for grounded RAG answers."""

from __future__ import annotations

from brainy.memory.store import MemoryStore
from brainy.memory.vectors import VectorStore
from brainy.router import ModelRouter

from .pipeline import Answer, ask


class RAGEngine:
    def __init__(self, store: MemoryStore, vectors: VectorStore, router: ModelRouter) -> None:
        self._store = store
        self._vectors = vectors
        self._router = router

    def answer(self, question: str, *, k: int | None = None, verify: bool = False) -> Answer:
        return ask(self._store, self._vectors, self._router, question, k=k, verify=verify)
