import pytest

from brainy.eval.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_ir_metrics_use_only_labelled_relevance():
    retrieved = ["wrong", "a", "b"]
    relevant = {"a", "b"}

    assert precision_at_k(retrieved, relevant, 2) == 0.5
    assert recall_at_k(retrieved, relevant, 3) == 1.0
    assert reciprocal_rank(retrieved, relevant) == 0.5
    assert 0.0 < ndcg_at_k(retrieved, relevant, 3) < 1.0


def test_precision_rejects_invalid_k():
    with pytest.raises(ValueError):
        precision_at_k([], set(), 0)
