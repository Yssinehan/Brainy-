"""Thin wrapper around Chroma - the only module that knows it's Chroma (ADR 0001)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from brainy.config import get_settings

_COLLECTION_NAME = "personal_llm_chunks"


class VectorStore:
    def __init__(self, persist_dir: str | None = None, *, in_memory: bool = False) -> None:
        import chromadb

        if in_memory:
            self._client = chromadb.EphemeralClient()
            # Chroma shares an EphemeralClient process-wide. A unique collection
            # prevents data from one unit-test fixture leaking into another.
            self._collection = self._client.get_or_create_collection(
                f"{_COLLECTION_NAME}_{uuid4().hex}"
            )
            return

        settings = get_settings()
        path = Path(persist_dir or settings.brainy_chroma_dir)
        # Chroma's Rust backend does not consistently create an absolute persistence
        # directory itself on Windows. Creating it here makes the storage boundary
        # reliable for normal starts and isolated test databases alike.
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)

    def add(self, ids: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        if not ids:
            return
        self._collection.add(ids=ids, embeddings=vectors, metadatas=metadatas)

    def query(self, vector: list[float], k: int = 8) -> list[tuple[str, float, dict]]:
        """Returns (id, similarity, metadata), similarity in [0, 1], highest first."""
        if self._collection.count() == 0:
            return []
        k = min(k, self._collection.count())
        result = self._collection.query(query_embeddings=[vector], n_results=k)
        ids = result["ids"][0]
        distances = result["distances"][0]
        metadatas = result["metadatas"][0]
        # Chroma default distance is squared L2 on normalized vectors; convert to a
        # bounded similarity score (1 = identical, 0 = dissimilar) for ranking.
        out = []
        for _id, dist, meta in zip(ids, distances, metadatas):
            similarity = max(0.0, 1.0 - dist / 2.0)
            out.append((_id, similarity, meta or {}))
        return out

    def count(self) -> int:
        return self._collection.count()

    def close(self) -> None:
        """Release the underlying sqlite handle.

        Chroma's PersistentClient keeps chroma.sqlite3 open until this is called (or
        the client is garbage-collected), which races a TemporaryDirectory's cleanup
        on Windows (WinError 32: file in use) - callers using a temp persist_dir must
        call this before the directory context exits.
        """
        self._client.close()
