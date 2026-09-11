from brainy.engine import Engine, PersonalAIEngine
from brainy.voice import SpeechToText, TextToSpeech


def _engine(store, vectors, router):
    return PersonalAIEngine(Engine(store=store, vectors=vectors, router=router, stt=SpeechToText(), tts=TextToSpeech()))


def test_personal_ai_engine_delegates_memory_retrieval(store, vectors, router):
    engine = _engine(store, vectors, router)
    remembered = engine.update_memory("Brainy is the user's PFA.")

    assert remembered.content == "Brainy is the user's PFA."
    assert engine.retrieve_context("Brainy") == []


def test_personal_ai_engine_queries_knowledge_graph(store, vectors, router):
    engine = _engine(store, vectors, router)

    assert engine.query_knowledge("Unknown entity") == []
