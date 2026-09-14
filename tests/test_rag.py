from brainy.memory.ingest import ingest_text
from types import SimpleNamespace

from brainy.rag.pipeline import NOT_IN_MEMORY, _build_context, ask
from brainy.router.schemas import Completion, Message, VerifiedCompletion


def test_ask_returns_grounded_answer_with_sources(store, vectors, router):
    ingest_text(
        store, vectors, router,
        text="Yassine is building Personal LLM, a local-first memory engine.",
        doc_id="doc-1", source="notes.md", extract_kg=False,
    )

    answer = ask(store, vectors, router, "What is Yassine building?")

    assert answer.grounded is True
    assert answer.text == router.canned_text
    assert len(answer.sources) >= 1
    assert answer.sources[0].source == "notes.md"


def test_ask_returns_not_in_memory_for_unrelated_question(store, vectors, router):
    ingest_text(
        store, vectors, router,
        text="Yassine is building Personal LLM.",
        doc_id="doc-1", source="notes.md", extract_kg=False,
    )

    answer = ask(store, vectors, router, "boiling point tungsten vacuum experiment reading")

    assert answer.grounded is False
    assert answer.text == NOT_IN_MEMORY
    assert answer.sources == []


def test_ask_removes_model_generated_source_line_from_display_text(store, vectors, router):
    ingest_text(store, vectors, router, text="Brainy uses local memory.", doc_id="doc-1", source="notes.md", extract_kg=False)
    router.canned_text = "Brainy uses local memory.\nSource : [6] (source: knowledge_base\\03_artificial_intelligence.md)"

    answer = ask(store, vectors, router, "How does Brainy work?")

    assert answer.text == "Brainy uses local memory."
    assert answer.sources[0].source == "notes.md"


def test_context_is_capped_to_keep_local_generation_fast():
    chunks = [SimpleNamespace(text="a" * 10), SimpleNamespace(text="b" * 10)]

    context = _build_context(chunks, max_chars=15)

    assert context == "a" * 10 + "\n\n" + "b" * 5


def test_ask_on_empty_memory_returns_not_in_memory(store, vectors, router):
    answer = ask(store, vectors, router, "anything at all")

    assert answer.grounded is False
    assert answer.text == NOT_IN_MEMORY


def test_planning_request_bypasses_memory_refusal_and_instructs_the_model(store, vectors, router):
    answer = ask(store, vectors, router, "Aide-moi à planifier mes activités de demain")

    assert answer.text == router.canned_text
    assert answer.grounded is False
    system_message = router.calls[0][0][0].content
    assert "Ne refuse jamais" in system_message
    assert "pose d'abord" in system_message


def test_planning_follow_up_keeps_the_planning_flow(store, vectors, router):
    history = [
        Message(role="user", content="Je veux organiser ma semaine."),
        Message(role="assistant", content="Quelles sont vos activités fixes ?"),
    ]

    answer = ask(store, vectors, router, "J'ai cours lundi à 9h et sport mardi soir.", history=history)

    assert answer.text == router.canned_text
    messages = router.calls[0][0]
    assert messages[1:-1] == history


def test_ask_verify_false_never_calls_verification(store, vectors, router):
    ingest_text(store, vectors, router, text="Yassine likes Python.", doc_id="doc-1", source="notes.md", extract_kg=False)

    answer = ask(store, vectors, router, "what does Yassine like?", verify=False)

    assert answer.disagreement is False
    assert answer.alternate_texts == []


def test_ask_verify_true_surfaces_disagreement(store, vectors, router):
    ingest_text(store, vectors, router, text="Yassine likes Python.", doc_id="doc-1", source="notes.md", extract_kg=False)
    router.verify_result = VerifiedCompletion(
        primary=Completion(text="Python", parsed=None, provider="fake-a", model="a"),
        alternates=[Completion(text="Rust", parsed=None, provider="fake-b", model="b")],
        agreement_scores=[0.1],
        disagreement=True,
    )

    answer = ask(store, vectors, router, "what does Yassine like?", verify=True)

    assert answer.text == "Python"
    assert answer.disagreement is True
    assert answer.alternate_texts == ["Rust"]
