"""Reproducible information-retrieval metrics for labelled evaluation sets."""

from __future__ import annotations

import math


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return sum(item in relevant for item in retrieved[:k]) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return sum(item in relevant for item in retrieved[:k]) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for index, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0 or not relevant:
        return 0.0
    dcg = sum(1.0 / math.log2(index + 1) for index, item in enumerate(retrieved[:k], start=1) if item in relevant)
    ideal_count = min(k, len(relevant))
    ideal = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_count + 1))
    return dcg / ideal if ideal else 0.0
