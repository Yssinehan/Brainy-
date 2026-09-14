"""The one place the rest of the engine calls out to a model.

Chat completion and embeddings are local. Ollama provides the chat model; OCR handles
image text locally without sending user data to a cloud service.
"""

from __future__ import annotations

import math

from pydantic import BaseModel

from .providers import ChatProvider, LocalEmbedder, OllamaProvider, RouterError
from .schemas import Completion, Message, VerifiedCompletion

__all__ = ["ModelRouter", "RouterError"]

_AGREEMENT_THRESHOLD = 0.6


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


class ModelRouter:
    def __init__(
        self,
        chat_providers: list[ChatProvider] | None = None,
        embedder: LocalEmbedder | None = None,
    ) -> None:
        self._ollama = OllamaProvider()
        # Chat is intentionally Ollama-only. Do not silently send prompts to a
        # cloud provider when the local endpoint is unavailable.
        self._chat_providers = chat_providers if chat_providers is not None else [self._ollama]
        self._embedder = embedder or LocalEmbedder()
        self._ollama_healthy: bool | None = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed(texts)

    def provider_status(self) -> dict[str, bool]:
        return {provider.name: self._provider_available(provider) for provider in self._chat_providers}

    def warmup(self) -> None:
        """Warm only the local chat model; embedding loading stays lazy until RAG is used."""
        if self._provider_available(self._ollama):
            self._ollama.warmup()

    def _provider_available(self, provider: ChatProvider) -> bool:
        if provider.name == "ollama":
            if self._ollama_healthy is None:
                self._ollama_healthy = provider.is_available()
            return self._ollama_healthy
        return provider.is_available()

    def complete(self, messages: list[Message], schema: type[BaseModel] | None = None) -> Completion:
        errors: list[str] = []
        for provider in self._chat_providers:
            if not self._provider_available(provider):
                errors.append(f"{provider.name}: not configured")
                continue
            try:
                return provider.complete(messages, schema=schema)
            except RouterError as exc:
                errors.append(f"{provider.name}: {exc}")
                continue
        raise RouterError(
            "No chat provider available. " + ("; ".join(errors) if errors else "Start Ollama and pull the configured model.")
        )

    def complete_with_verification(
        self, messages: list[Message], schema: type[BaseModel] | None = None
    ) -> VerifiedCompletion:
        """Query every currently-available provider (not just the first healthy one) and
        flag disagreement via embedding similarity - a free, local 'second opinion' check
        (ADR 0004). Falls back to a single completion when only one provider is available."""
        completions: list[Completion] = []
        errors: list[str] = []
        for provider in self._chat_providers:
            if not self._provider_available(provider):
                continue
            try:
                completions.append(provider.complete(messages, schema=schema))
            except RouterError as exc:
                errors.append(f"{provider.name}: {exc}")
                continue

        if not completions:
            raise RouterError(
                "No chat provider available for verification. "
                + ("; ".join(errors) if errors else "Start Ollama and pull the configured model.")
            )

        primary, *alternates = completions
        if not alternates:
            return VerifiedCompletion(primary=primary)

        primary_vector = self.embed([primary.text])[0]
        scores = []
        disagreement = False
        for alt in alternates:
            alt_vector = self.embed([alt.text])[0]
            score = _cosine(primary_vector, alt_vector)
            scores.append(score)
            if score < _AGREEMENT_THRESHOLD:
                disagreement = True

        return VerifiedCompletion(primary=primary, alternates=alternates, agreement_scores=scores, disagreement=disagreement)
