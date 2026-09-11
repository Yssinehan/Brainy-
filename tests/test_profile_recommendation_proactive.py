from datetime import datetime, timedelta, timezone

from brainy.memory.types import MemoryRecord
from brainy.profile import PersonalProfile
from brainy.proactive import ProactiveAssistant
from brainy.recommendation import RecommendationEngine


def test_profile_uses_only_persisted_memory_evidence(store):
    store.add_memory(MemoryRecord(kind="fact", source="user", content="I prefer concise Python explanations.", meta={"project": "Brainy"}))

    profile = PersonalProfile(store).build()

    assert profile.projects == ["Brainy"]
    assert "concise" in profile.frequent_topics


def test_recommendations_have_a_data_backed_rationale(store):
    store.add_memory(MemoryRecord(content="hybrid rag retrieval"))

    recommendations = RecommendationEngine(store).generate()

    assert recommendations and "persisted memory" in recommendations[0].rationale


def test_proactive_assistant_reports_inactive_project(store):
    old = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat()
    store.add_memory(MemoryRecord(content="Brainy task", created_at=old, meta={"project": "Brainy"}))

    insights = ProactiveAssistant(store).inspect()

    assert insights and insights[0].kind == "inactive_project"
