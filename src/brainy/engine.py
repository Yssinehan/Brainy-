"""Shared bootstrap so CLI, API, and Streamlit all wire up the same engine the same way."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from brainy.config import get_settings
from brainy.agent import Agent, AgentResult
from brainy.graph import KnowledgeGraph
from brainy.memory import MemoryManager, MemoryRecord
from brainy.memory.ingest import IngestResult
from brainy.memory.store import MemoryStore
from brainy.memory.vectors import VectorStore
from brainy.proactive import ProactiveAssistant, ProactiveInsight
from brainy.profile import PersonalProfile, ProfileSnapshot
from brainy.rag import Answer, RAGEngine
from brainy.recommendation import Recommendation, RecommendationEngine
from brainy.review.weekly import ReviewReport, generate_review
from brainy.router import ModelRouter
from brainy.tools import build_default_registry
from brainy.voice import SpeechToText, TextToSpeech

log = logging.getLogger("brainy")
_SESSION_ID = uuid.uuid4().hex


@dataclass
class Engine:
    store: MemoryStore
    vectors: VectorStore
    router: ModelRouter
    stt: SpeechToText
    tts: TextToSpeech


class PersonalAIEngine:
    """Coordinates Brainy's domain services without owning their internal logic.

    ``Engine`` remains the dependency container used by existing callers. This class
    is the incremental migration target for CLI, API, and UI clients.
    """

    def __init__(self, dependencies: Engine) -> None:
        self._dependencies = dependencies
        self.memory = MemoryManager(dependencies.store, dependencies.vectors, dependencies.router)
        self.rag = RAGEngine(dependencies.store, dependencies.vectors, dependencies.router)
        self.knowledge = KnowledgeGraph(dependencies.store)
        self.profile = PersonalProfile(dependencies.store)
        self.recommendations = RecommendationEngine(dependencies.store, self.profile)
        self.proactive = ProactiveAssistant(dependencies.store)
        self.conversation_id = _SESSION_ID

    def process_message(self, message: str, *, k: int | None = None, verify: bool = False) -> Answer:
        log.info("request chat verify=%s", verify)
        answer = self.generate_response(message, k=k, verify=verify)
        log.info("response grounded=%s sources=%s", answer.grounded, len(answer.sources))
        return answer

    def retrieve_context(self, query: str, *, k: int | None = None):
        return self.memory.retrieve(query, k=k)

    def update_memory(self, content: str, *, importance: float = 0.7, source: str = "user") -> MemoryRecord:
        return self.memory.remember(content, importance=importance, source=source)

    def query_knowledge(self, entity: str, *, hops: int = 1) -> list[dict]:
        return self.knowledge.query(entity, hops=hops)

    def invoke_agent(
        self, goal: str, *, allow_network: bool = False, allow_write: bool = False, max_steps: int | None = None
    ) -> AgentResult:
        settings = get_settings()
        allowed = {"read_only"}
        if allow_network:
            allowed.add("network")
        if allow_write:
            allowed.add("read_write")
        registry = build_default_registry(
            self._dependencies.store, self._dependencies.vectors, self._dependencies.router, settings.brainy_workspace_dir
        )
        log.info("request agent network=%s write=%s", allow_network, allow_write)
        agent = Agent(
            self._dependencies.router,
            registry,
            self._dependencies.store,
            allowed_permissions=allowed,
            max_steps=max_steps or settings.agent_max_steps,
        )
        result = agent.run(goal)
        log.info("response agent succeeded=%s steps=%s", result.succeeded, len(result.steps))
        return result

    def ingest_text(self, text: str, *, doc_id: str, source: str = "user") -> IngestResult:
        return self.memory.ingest(text, doc_id=doc_id, source=source)

    def stats(self) -> dict:
        return self.memory.stats()

    def build_profile(self) -> ProfileSnapshot:
        return self.profile.build()

    def recommend(self, *, limit: int = 5) -> list[Recommendation]:
        return self.recommendations.generate(limit=limit)

    def inspect_proactive(self, *, limit: int = 5) -> list[ProactiveInsight]:
        return self.proactive.inspect(limit=limit)

    def generate_response(self, message: str, *, k: int | None = None, verify: bool = False) -> Answer:
        return self.rag.answer(message, k=k, verify=verify)

    def trigger_proactive_actions(self, *, days: int = 7) -> ReviewReport:
        return generate_review(self._dependencies.store, self._dependencies.router, days=days)


_engine: Engine | None = None


def build_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = Engine(
            store=MemoryStore(settings.brainy_db_path),
            vectors=VectorStore(settings.brainy_chroma_dir),
            router=ModelRouter(),
            stt=SpeechToText(),
            tts=TextToSpeech(),
        )
    return _engine


def build_personal_ai_engine() -> PersonalAIEngine:
    """Build the orchestration façade over the shared dependency container."""
    return PersonalAIEngine(build_engine())
