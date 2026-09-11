from brainy.config import Settings
from brainy.memory.scoring import score_memory
from brainy.memory.types import MemoryRecord


def test_score_memory_exposes_all_configured_factors():
    memory = MemoryRecord(
        content="User prefers concise answers.", source="user", importance=0.8, access_count=3,
        meta={"confidence": 0.9, "source_reliability": 0.9},
    )

    score = score_memory(memory, relevance=0.7, recency=0.6, settings=Settings())

    assert score.relevance == 0.7
    assert score.confidence == 0.9
    assert score.user_interaction == 1.0
    assert 0.0 < score.total <= 1.0


def test_score_memory_honors_central_weight_configuration():
    memory = MemoryRecord(content="A fact", importance=0.0, meta={"confidence": 0.0, "source_reliability": 0.0})
    settings = Settings(memory_score_relevance_weight=1.0, memory_score_importance_weight=0.0,
                        memory_score_recency_weight=0.0, memory_score_frequency_weight=0.0,
                        memory_score_confidence_weight=0.0, memory_score_source_reliability_weight=0.0,
                        memory_score_user_interaction_weight=0.0)

    assert score_memory(memory, relevance=0.73, recency=0.0, settings=settings).total == 0.73
