"""Retrieve -> ground -> answer, with an honest "not in memory" path (docs/TDD.md section 3)."""

from __future__ import annotations

import logging
import re
import time
from collections import OrderedDict

from pydantic import BaseModel, Field

from brainy.config import get_settings
from brainy.memory.store import MemoryStore
from brainy.memory.types import MemoryRecord
from brainy.memory.vectors import VectorStore
from brainy.prompts import load_prompt
from brainy.router import Message, ModelRouter
from brainy.router.schemas import Completion
from brainy.rag.retrievers import HybridRetriever
from brainy.rag.temporal import filter_recent

NOT_IN_MEMORY = "I don't have anything in memory about that."
log = logging.getLogger("brainy")
_MODEL_SOURCE_LINE = re.compile(r"(?im)^\s*source\s*:\s*\[\d+\]\s*\(source:\s*.+?\)\s*$")
_GENERAL_QUESTION = re.compile(
    r"^\s*(?:bonjour|bonsoir|salut|coucou|merci|comment (?:ça|ca) va|qui es[- ]tu|"
    r"qu['’]est[- ]ce que (?:l['’]?)?(?:intelligence artificielle|machine learning)|"
    r"comment organiser mes révisions)\b",
    re.I,
)
_PLANNING_REQUEST = re.compile(
    r"\b(?:planifier|planning|plan\b|organis(?:er|ation)|emploi du temps|activit[ée]s?|"
    r"journ[ée]e|demain|semaine|r[ée]visions?)\b",
    re.I,
)
_ANSWER_CACHE: OrderedDict[str, tuple[float, Answer]] = OrderedDict()
_CACHE_TTL_SECONDS = 300
_CACHE_MAX_ITEMS = 64


class Source(BaseModel):
    doc_id: str
    source: str
    snippet: str


class Answer(BaseModel):
    text: str
    sources: list[Source] = Field(default_factory=list)
    grounded: bool = True
    disagreement: bool = False
    alternate_texts: list[str] = Field(default_factory=list)


def _build_context(chunks, max_chars: int) -> str:
    """Build a bounded context so local CPU inference stays responsive."""
    blocks = []
    remaining = max_chars
    for chunk in chunks:
        if remaining <= 0:
            break
        excerpt = chunk.text[:remaining].strip()
        if excerpt:
            blocks.append(excerpt)
            remaining -= len(excerpt)
    return "\n\n".join(blocks)


def _without_model_source_lines(text: str) -> str:
    """Keep retrieval provenance in ``Answer.sources``, not in the user-facing reply."""
    return _MODEL_SOURCE_LINE.sub("", text).strip()


def _is_general_question(question: str) -> bool:
    """Questions with no dependence on user documents should bypass retrieval."""
    return bool(_GENERAL_QUESTION.search(question.strip()))


def _is_planning_request(question: str, history: list[Message] | None = None) -> bool:
    """Keep a planning exchange out of the memory-only RAG refusal path."""
    prior_user_messages = " ".join(message.content for message in history or [] if message.role == "user")
    return bool(_PLANNING_REQUEST.search(f"{prior_user_messages} {question}"))


def _planning_system_prompt() -> str:
    return (
        "Tu es Brainy, un assistant personnel d'organisation. Tu aides toujours l'utilisateur "
        "à planifier ses journées, ses semaines, ses révisions et ses activités. Ne refuse jamais "
        "une demande de planning. Si les informations nécessaires manquent, pose d'abord au maximum "
        "trois questions courtes et précises sur la date ou la période, les activités fixes, les "
        "priorités, les durées et les contraintes. Dès que les informations sont suffisantes, propose "
        "un planning détaillé, réaliste et ordonné par horaire, avec des pauses. N'invente pas "
        "d'activités ni de disponibilités : indique clairement les hypothèses et demande confirmation "
        "avant de considérer le planning définitif. Réponds en français, de manière concise."
    )


def _cached_answer(question: str) -> Answer | None:
    key = question.strip().casefold()
    item = _ANSWER_CACHE.get(key)
    if item is None or time.monotonic() - item[0] > _CACHE_TTL_SECONDS:
        _ANSWER_CACHE.pop(key, None)
        return None
    _ANSWER_CACHE.move_to_end(key)
    return item[1].model_copy(deep=True)


def _cache_answer(question: str, answer: Answer) -> None:
    _ANSWER_CACHE[question.strip().casefold()] = (time.monotonic(), answer.model_copy(deep=True))
    _ANSWER_CACHE.move_to_end(question.strip().casefold())
    while len(_ANSWER_CACHE) > _CACHE_MAX_ITEMS:
        _ANSWER_CACHE.popitem(last=False)


def ask(
    store: MemoryStore,
    vectors: VectorStore,
    router: ModelRouter,
    question: str,
    k: int | None = None,
    verify: bool = False,
    history: list[Message] | None = None,
) -> Answer:
    started = time.perf_counter()
    settings = get_settings()
    is_planning = _is_planning_request(question, history)
    if not verify and (_is_general_question(question) or is_planning):
        cached = _cached_answer(question)
        if cached:
            log.info("[PERF] Cache: %.1f ms | Total: %.1f ms", 0.0, (time.perf_counter() - started) * 1000)
            return cached
        system = _planning_system_prompt() if is_planning else "Tu es Brainy, un assistant étudiant. Réponds clairement, directement et brièvement."
        messages = [Message(role="system", content=system), *(history or [])[-8:], Message(role="user", content=question)]
        llm_started = time.perf_counter()
        completion = router.complete(messages)
        answer = Answer(text=_without_model_source_lines(completion.text), sources=[], grounded=False)
        if not history:
            _cache_answer(question, answer)
        total = (time.perf_counter() - started) * 1000
        log.info("[PERF] RAG: 0.0 ms | Embeddings: 0.0 ms | ChromaDB: 0.0 ms | SQLite: 0.0 ms | Context: 0.0 ms | Ollama: %.1f ms | Total: %.1f ms", (time.perf_counter() - llm_started) * 1000, total)
        return answer

    retrieval_started = time.perf_counter()
    chunks = HybridRetriever(store, vectors, router).retrieve(question, k=k or settings.retrieval_top_k)
    chunks = filter_recent(chunks, question)
    rag_ms = (time.perf_counter() - retrieval_started) * 1000
    log.info("retrieval hits=%s", len(chunks))

    top_similarity = chunks[0].similarity if chunks else 0.0
    if not chunks or top_similarity < settings.retrieval_min_similarity:
        store.log("system", "ask", {"question": question, "grounded": False})
        log.info("rag not_in_memory")
        log.info("[PERF] RAG: %.1f ms | Context: 0.0 ms | Ollama: 0.0 ms | Total: %.1f ms", rag_ms, (time.perf_counter() - started) * 1000)
        return Answer(text=NOT_IN_MEMORY, sources=[], grounded=False)

    context_started = time.perf_counter()
    context = _build_context(chunks, settings.rag_context_max_chars)
    messages = [
        Message(role="system", content=load_prompt("rag_system")),
        Message(role="user", content=f"<context>\n{context}\n</context>\n\nQuestion: {question}"),
    ]

    disagreement = False
    alternate_texts: list[str] = []
    if verify:
        verified = router.complete_with_verification(messages)
        completion: Completion = verified.primary
        disagreement = verified.disagreement
        alternate_texts = [alt.text for alt in verified.alternates]
    else:
        llm_started = time.perf_counter()
        completion = router.complete(messages)
    llm_ms = (time.perf_counter() - llm_started) * 1000 if not verify else 0.0
    log.info("llm provider=%s", completion.provider)

    store.add_memory(
        MemoryRecord(kind="episodic", content=f"Asked: {question}", source="chat", importance=0.4)
    )
    store.log(
        "system",
        "ask",
        {"question": question, "grounded": True, "provider": completion.provider, "verify": verify, "disagreement": disagreement},
    )

    sources = [Source(doc_id=c.doc_id, source=c.source, snippet=c.text[:200]) for c in chunks]
    log.info("[PERF] RAG: %.1f ms | Context: %.1f ms | Ollama: %.1f ms | Total: %.1f ms", rag_ms, (time.perf_counter() - context_started) * 1000 - llm_ms, llm_ms, (time.perf_counter() - started) * 1000)
    return Answer(
        text=_without_model_source_lines(completion.text),
        sources=sources,
        grounded=True,
        disagreement=disagreement,
        alternate_texts=alternate_texts,
    )
