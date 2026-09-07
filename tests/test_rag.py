from brainy.memory.ingest import ingest_text
from brainy.rag.pipeline import NOT_IN_MEMORY, ask
from brainy.router.schemas import Completion, VerifiedCompletion


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


def test_ask_on_empty_memory_returns_not_in_memory(store, vectors, router):
    answer = ask(store, vectors, router, "anything at all")

    assert answer.grounded is False
    assert answer.text == NOT_IN_MEMORY


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
