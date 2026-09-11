"""Composable retrieval strategies used by the hybrid RAG engine."""

from __future__ import annotations

import re
from collections import defaultdict

from brainy.memory.retrieve import RetrievedChunk, semantic_search
from brainy.memory.store import MemoryStore
from brainy.memory.vectors import VectorStore
from brainy.router import ModelRouter

_WORD = re.compile(r"[\w'-]+", re.UNICODE)


def _terms(text: str) -> set[str]:
    return {word.lower() for word in _WORD.findall(text) if len(word) >= 3}


class KeywordRetriever:
    """Dependency-free lexical retrieval over the canonical chunk store."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def retrieve(self, query: str, *, k: int = 8) -> list[RetrievedChunk]:
        terms = _terms(query)
        if not terms:
            return []
        memories = self._store.get_memories_by_vector_ids([c.id for c in self._store.all_chunks()])
        hits: list[RetrievedChunk] = []
        for chunk in self._store.all_chunks():
            overlap = len(terms & _terms(chunk.text))
            if not overlap:
                continue
            memory = memories.get(chunk.id)
            similarity = overlap / len(terms)
            hits.append(RetrievedChunk(
                chunk_id=chunk.id, doc_id=chunk.doc_id, text=chunk.text,
                source=memory.source if memory else chunk.doc_id, similarity=similarity,
                importance=memory.importance if memory else 0.5, rank_score=similarity,
                created_at=memory.created_at if memory else chunk.created_at,
            ))
        return sorted(hits, key=lambda hit: hit.rank_score, reverse=True)[:k]


class GraphRetriever:
    """Uses KG provenance to recover source chunks for named query entities."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def retrieve(self, query: str, *, k: int = 8) -> list[RetrievedChunk]:
        query_terms = _terms(query)
        nodes = self._store.all_nodes()
        matched = [node for node in nodes if _terms(node.name) and _terms(node.name).issubset(query_terms)]
        if not matched:
            return []
        chunk_ids: set[str] = set()
        for edge in self._store.all_edges():
            if edge.src in {node.id for node in matched} or edge.dst in {node.id for node in matched}:
                chunk_id = str(edge.meta.get("chunk_id", ""))
                if chunk_id:
                    chunk_ids.add(chunk_id)
        chunks = self._store.get_chunks(sorted(chunk_ids))[:k]
        memories = self._store.get_memories_by_vector_ids([chunk.id for chunk in chunks])
        return [
            RetrievedChunk(
                chunk_id=chunk.id, doc_id=chunk.doc_id, text=chunk.text,
                source=memories[chunk.id].source if chunk.id in memories else chunk.doc_id,
                similarity=1.0, importance=memories[chunk.id].importance if chunk.id in memories else 0.5,
                rank_score=1.0, created_at=memories[chunk.id].created_at if chunk.id in memories else chunk.created_at,
            )
            for chunk in chunks
        ]


class HybridRetriever:
    """Fuses vector, keyword and graph rankings with reciprocal-rank fusion."""

    def __init__(self, store: MemoryStore, vectors: VectorStore, router: ModelRouter) -> None:
        self._store = store
        self._vectors = vectors
        self._router = router
        self._keyword = KeywordRetriever(store)
        self._graph = GraphRetriever(store)

    def retrieve(self, query: str, *, k: int = 8) -> list[RetrievedChunk]:
        rankings = [
            semantic_search(self._store, self._vectors, self._router, query, k=k),
            self._keyword.retrieve(query, k=k),
            self._graph.retrieve(query, k=k),
        ]
        scores: defaultdict[str, float] = defaultdict(float)
        candidates: dict[str, RetrievedChunk] = {}
        for ranking in rankings:
            for position, result in enumerate(ranking, start=1):
                scores[result.chunk_id] += 1.0 / (60 + position)
                candidates.setdefault(result.chunk_id, result)
        merged = []
        for chunk_id, score in scores.items():
            result = candidates[chunk_id].model_copy(update={"rank_score": score})
            merged.append(result)
        return sorted(merged, key=lambda result: result.rank_score, reverse=True)[:k]
