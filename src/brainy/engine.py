"""Shared bootstrap so CLI, API, and Streamlit all wire up the same engine the same way."""

from __future__ import annotations

from dataclasses import dataclass

from brainy.config import get_settings
from brainy.memory.store import MemoryStore
from brainy.memory.vectors import VectorStore
from brainy.router import ModelRouter
from brainy.voice import SpeechToText, TextToSpeech


@dataclass
class Engine:
    store: MemoryStore
    vectors: VectorStore
    router: ModelRouter
    stt: SpeechToText
    tts: TextToSpeech


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
