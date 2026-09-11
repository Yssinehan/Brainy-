"""Configurable, explainable memory-ranking functions."""

from __future__ import annotations

import math
from dataclasses import dataclass

from brainy.config import Settings

from .types import MemoryRecord


@dataclass(frozen=True)
class MemoryScore:
    relevance: float
    importance: float
    recency: float
    frequency: float
    confidence: float
    source_reliability: float
    user_interaction: float
    total: float


def score_memory(memory: MemoryRecord | None, *, relevance: float, recency: float, settings: Settings) -> MemoryScore:
    """Score a retrieved memory using one centrally-configured weight set."""
    meta = memory.meta if memory is not None else {}
    importance = memory.importance if memory is not None else 0.5
    frequency = min(1.0, math.log1p(memory.access_count) / math.log(11)) if memory else 0.0
    confidence = float(meta.get("confidence", 1.0))
    source_reliability = float(meta.get("source_reliability", 0.5))
    user_interaction = 1.0 if memory and memory.source in {"user", "chat", "agent"} else 0.0
    weights = {
        "relevance": settings.memory_score_relevance_weight,
        "importance": settings.memory_score_importance_weight,
        "recency": settings.memory_score_recency_weight,
        "frequency": settings.memory_score_frequency_weight,
        "confidence": settings.memory_score_confidence_weight,
        "source_reliability": settings.memory_score_source_reliability_weight,
        "user_interaction": settings.memory_score_user_interaction_weight,
    }
    factors = {
        "relevance": max(0.0, min(1.0, relevance)),
        "importance": max(0.0, min(1.0, importance)),
        "recency": max(0.0, min(1.0, recency)),
        "frequency": frequency,
        "confidence": max(0.0, min(1.0, confidence)),
        "source_reliability": max(0.0, min(1.0, source_reliability)),
        "user_interaction": user_interaction,
    }
    denominator = sum(weights.values())
    total = sum(factors[name] * weights[name] for name in factors) / denominator if denominator else 0.0
    return MemoryScore(**factors, total=total)
