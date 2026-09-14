"""Concrete providers behind the router. Only this module talks to the network."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel

from brainy.config import get_settings

from .schemas import Completion, Message

class RouterError(Exception):
    """User-facing error the caller can display verbatim."""


class ChatProvider(Protocol):
    name: str

    def complete(self, messages: list[Message], schema: type[BaseModel] | None = None) -> Completion: ...

    def is_available(self) -> bool: ...


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(
                host=self._settings.ollama_host,
                timeout=self._settings.ollama_timeout_seconds,
            )
        return self._client

    def is_available(self) -> bool:
        try:
            import httpx

            resp = httpx.get(f"{self._settings.ollama_host}/api/tags", timeout=1.0)
            return resp.status_code == 200
        except Exception:
            return False

    def warmup(self) -> None:
        """Ask Ollama to keep the configured model resident before the first chat."""
        try:
            import httpx
            httpx.post(
                f"{self._settings.ollama_host}/api/generate",
                json={"model": self._settings.ollama_model, "prompt": "", "stream": False,
                      "keep_alive": self._settings.ollama_keep_alive},
                timeout=self._settings.ollama_timeout_seconds,
            ).raise_for_status()
        except Exception as exc:
            # A missing Ollama must not prevent the web interface from starting.
            raise RouterError(f"Ollama warmup failed: {exc}") from exc

    def complete(self, messages: list[Message], schema: type[BaseModel] | None = None) -> Completion:
        client = self._get_client()
        # A CPU-hosted local model may otherwise generate until it emits an EOS token,
        # leaving the browser waiting indefinitely for a response.
        options: dict[str, int] = {
            "num_predict": self._settings.ollama_max_tokens,
            "num_ctx": self._settings.ollama_num_ctx,
        }
        if self._settings.ollama_num_thread > 0:
            options["num_thread"] = self._settings.ollama_num_thread
        kwargs: dict = {"options": options, "keep_alive": self._settings.ollama_keep_alive}
        if schema is not None:
            kwargs["format"] = schema.model_json_schema()

        try:
            response = client.chat(
                model=self._settings.ollama_model,
                messages=[m.model_dump() for m in messages],
                **kwargs,
            )
        except Exception as exc:
            raise RouterError(f"Ollama call failed: {exc}")

        text = response["message"]["content"]
        parsed = None
        if schema is not None:
            try:
                parsed = schema(**json.loads(text))
            except (json.JSONDecodeError, ValueError):
                parsed = None
        return Completion(text=text, parsed=parsed, provider=self.name, model=self._settings.ollama_model)


class LocalEmbedder:
    """Free, offline embeddings via sentence-transformers. Loaded lazily (slow import)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._settings.embedding_model)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.tolist()
