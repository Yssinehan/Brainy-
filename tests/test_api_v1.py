from fastapi.testclient import TestClient

from brainy.engine import Engine
from brainy.interfaces import api
from brainy.voice import SpeechToText, TextToSpeech


def test_v1_profile_requires_gateway_token(monkeypatch, store, vectors, router):
    engine = Engine(store=store, vectors=vectors, router=router, stt=SpeechToText(), tts=TextToSpeech())
    monkeypatch.setattr(api, "build_engine", lambda: engine)
    monkeypatch.setattr(api, "_load_or_create_gateway_token", lambda: "token")

    client = TestClient(api.app)
    assert client.get("/api/v1/profile").status_code == 401
    assert client.get("/api/v1/profile", headers={api.GATEWAY_TOKEN_HEADER: "token"}).status_code == 200
