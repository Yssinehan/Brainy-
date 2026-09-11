"""FastAPI surface - the stable HTTP API non-Python callers use (docs/TDD.md section 8)."""

from __future__ import annotations

import json
import logging
import secrets
import tempfile
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from brainy import __version__
from brainy.agent import AgentResult
from brainy.config import get_settings
from brainy.engine import PersonalAIEngine, build_engine
from brainy.integrations import ExternalItem, SyncResult, sync_external_items
from brainy.memory.ingest import IngestResult
from brainy.memory.retrieve import RetrievedChunk
from brainy.proactive import ProactiveInsight
from brainy.profile import ProfileSnapshot
from brainy.rag.pipeline import Answer, Source
from brainy.recommendation import Recommendation
from brainy.review.weekly import ReviewReport
from brainy.router.providers import RouterError
from brainy.vision import VisionError

log = logging.getLogger("brainy")

app = FastAPI(title="Personal LLM", version=__version__)
v1 = APIRouter(prefix="/api/v1")
WEB_DIR = Path(__file__).with_name("web")
app.mount("/ui", StaticFiles(directory=WEB_DIR), name="brainy-ui")

GATEWAY_TOKEN_HEADER = "x-dreamos-token"
_gateway_token: str | None = None


def _load_or_create_gateway_token() -> str:
    """Shared secret DreamOS (or any other local caller) must send back on every request.

    Generated once and persisted to disk so it survives a gateway restart without the
    caller needing to re-pair.
    """
    global _gateway_token
    if _gateway_token is not None:
        return _gateway_token
    path = Path(get_settings().brainy_gateway_token_path)
    existing = path.read_text().strip() if path.exists() else ""
    if existing:
        _gateway_token = existing
    else:
        _gateway_token = secrets.token_hex(32)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_gateway_token)
    return _gateway_token


@app.middleware("http")
async def gateway_auth(request: Request, call_next):
    """Protect API calls while allowing the bundled, same-origin local UI.

    The page and its static assets are public only so the browser can load the
    gateway token embedded into the locally served page. All API calls still
    require that token; an Origin header is accepted only when it exactly
    matches this request's host and scheme, so external browser pages remain
    blocked.
    """
    if request.url.path in {"/", "/health"} or request.url.path.startswith("/ui/"):
        return await call_next(request)

    origin = request.headers.get("origin")
    expected_origin = f"{request.url.scheme}://{request.headers.get('host', '')}"
    if origin and not secrets.compare_digest(origin.rstrip("/"), expected_origin.rstrip("/")):
        return JSONResponse(status_code=403, content={"detail": "Cross-origin requests are not allowed."})
    if request.headers.get(GATEWAY_TOKEN_HEADER) != _load_or_create_gateway_token():
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid X-DreamOS-Token."})
    return await call_next(request)


async def _save_upload_to_temp(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await upload.read())
        return tmp.name


def _ai() -> PersonalAIEngine:
    return PersonalAIEngine(build_engine())


def _user_error(detail: object) -> str:
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            location = " ".join(str(part) for part in first.get("loc", ()) if part != "body")
            message = first.get("msg", "Requête invalide.")
            return f"{location}: {message}" if location else message
        return str(first)
    return "La requête n’a pas pu être traitée."


@app.exception_handler(RouterError)
async def router_unavailable(_request: Request, exc: RouterError) -> JSONResponse:
    log.warning("llm unavailable: %s", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": _user_error(exc.errors())})


class IngestRequest(BaseModel):
    text: str
    doc_id: str
    source: str = "api"


class AskRequest(BaseModel):
    question: str
    k: int | None = None
    verify: bool = False


class VoiceAnswer(Answer):
    """A grounded answer paired with the browser-visible audio transcript."""

    transcript: str


class RememberRequest(BaseModel):
    fact: str
    importance: float = 0.7


class AgentRunRequest(BaseModel):
    goal: str
    allow_network: bool = False
    allow_write: bool = False
    max_steps: int = 6


class ReviewRequest(BaseModel):
    days: int = 7


class IntegrationsSyncRequest(BaseModel):
    items: list[ExternalItem]


class ChatRequest(BaseModel):
    message: str
    k: int | None = None
    verify: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: list[Source]
    memory_used: bool
    grounded: bool
    disagreement: bool = False
    text: str


def _chat_response(answer: Answer, conversation_id: str) -> ChatResponse:
    return ChatResponse(
        response=answer.text,
        conversation_id=conversation_id,
        sources=answer.sources,
        memory_used=bool(answer.sources) or answer.grounded,
        grounded=answer.grounded,
        disagreement=answer.disagreement,
        text=answer.text,
    )


@v1.post("/chat", response_model=ChatResponse)
def v1_chat(req: ChatRequest) -> ChatResponse:
    engine = _ai()
    answer = engine.process_message(req.message, k=req.k, verify=req.verify)
    return _chat_response(answer, engine.conversation_id)


@v1.post("/rag/ask", response_model=Answer)
def v1_rag_ask(req: AskRequest) -> Answer:
    return _ai().process_message(req.question, k=req.k, verify=req.verify)


@v1.post("/memory/remember")
def v1_remember(req: RememberRequest) -> dict:
    record = _ai().update_memory(req.fact, importance=req.importance)
    return {"id": record.id}


@v1.get("/memory/recall", response_model=list[RetrievedChunk])
def v1_recall(q: str, k: int = 5) -> list[RetrievedChunk]:
    return _ai().retrieve_context(q, k=k)


@v1.get("/knowledge/{entity}")
def v1_knowledge(entity: str, hops: int = 1) -> list[dict]:
    return _ai().query_knowledge(entity, hops=hops)


@v1.get("/profile", response_model=ProfileSnapshot)
def v1_profile() -> ProfileSnapshot:
    return _ai().build_profile()


@v1.get("/recommendations", response_model=list[Recommendation])
def v1_recommendations(limit: int = 5) -> list[Recommendation]:
    return _ai().recommend(limit=limit)


@v1.get("/proactive", response_model=list[ProactiveInsight])
def v1_proactive(limit: int = 5) -> list[ProactiveInsight]:
    return _ai().inspect_proactive(limit=limit)


@v1.post("/agent/run", response_model=AgentResult)
def v1_agent_run(req: AgentRunRequest) -> AgentResult:
    return _ai().invoke_agent(
        req.goal, allow_network=req.allow_network, allow_write=req.allow_write, max_steps=req.max_steps
    )


@app.post("/ingest", response_model=IngestResult)
def ingest_endpoint(req: IngestRequest) -> IngestResult:
    return _ai().ingest_text(req.text, doc_id=req.doc_id, source=req.source)


@app.post("/ask", response_model=Answer)
def ask_endpoint(req: AskRequest) -> Answer:
    return _ai().process_message(req.question, k=req.k, verify=req.verify)


@app.post("/memory/remember")
def remember_endpoint(req: RememberRequest) -> dict:
    record = _ai().update_memory(req.fact, importance=req.importance)
    return {"id": record.id}


@app.get("/memory/recall", response_model=list[RetrievedChunk])
def recall_endpoint(q: str, k: int = 5) -> list[RetrievedChunk]:
    return _ai().retrieve_context(q, k=k)


@app.post("/agent/run", response_model=AgentResult)
def agent_run_endpoint(req: AgentRunRequest) -> AgentResult:
    return _ai().invoke_agent(
        req.goal, allow_network=req.allow_network, allow_write=req.allow_write, max_steps=req.max_steps
    )


@app.post("/review/run", response_model=ReviewReport)
def review_endpoint(req: ReviewRequest) -> ReviewReport:
    return _ai().trigger_proactive_actions(days=req.days)


@app.post("/integrations/sync", response_model=SyncResult)
def integrations_sync_endpoint(req: IntegrationsSyncRequest) -> SyncResult:
    engine = build_engine()
    return sync_external_items(engine.store, engine.vectors, engine.router, req.items)


def _transcribe_or_400(engine, tmp_path: str) -> str:
    """Undecodable or silent audio must be a clear 400, never a crashed request.

    The av.open pre-check matters: feeding non-audio bytes straight into whisper can
    hard-crash the worker process (not a catchable exception), so validate first.
    """
    try:
        import av

        with av.open(tmp_path) as container:
            if not container.streams.audio:
                raise ValueError("no audio stream")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="That did not decode as audio - record a bit longer and try again.",
        )
    try:
        text = engine.stt.transcribe(tmp_path)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not decode the audio - record a bit longer and try again. ({type(exc).__name__})",
        )
    if not text.strip():
        raise HTTPException(status_code=400, detail="I heard nothing - hold to talk, speak, then release.")
    return text


@app.post("/voice/transcribe")
async def voice_transcribe_endpoint(file: UploadFile = File(...)) -> dict:
    engine = build_engine()
    tmp_path = await _save_upload_to_temp(file)
    try:
        return {"text": _transcribe_or_400(engine, tmp_path)}
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/voice/ask", response_model=VoiceAnswer)
async def voice_ask_endpoint(file: UploadFile = File(...), verify: bool = False) -> VoiceAnswer:
    engine = build_engine()
    tmp_path = await _save_upload_to_temp(file)
    try:
        question = _transcribe_or_400(engine, tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    answer = _ai().process_message(question, verify=verify)
    return VoiceAnswer(**answer.model_dump(), transcript=question)


@app.post("/vision/describe")
async def vision_describe_endpoint(file: UploadFile = File(...), question: str | None = None) -> dict:
    engine = build_engine()
    tmp_path = await _save_upload_to_temp(file)
    try:
        description = engine.router.describe_image(tmp_path, question)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return {"description": description}


@app.post("/vision/ingest")
async def vision_ingest_endpoint(file: UploadFile = File(...), doc_id: str | None = None) -> IngestResult:
    tmp_path = await _save_upload_to_temp(file)
    try:
        from brainy.vision.ocr import extract_text_from_image

        text = extract_text_from_image(tmp_path)
    except VisionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return _ai().ingest_text(text, doc_id=doc_id or (file.filename or "image"), source=file.filename or "image")


@app.get("/stats")
def stats_endpoint() -> dict:
    return _ai().stats()


@app.get("/health")
def health_endpoint() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
def web_interface() -> HTMLResponse:
    """Serve the local browser UI and inject its per-install gateway token.

    Serving it from this process makes its fetches same-origin. The token is
    not exposed through a standalone API endpoint and is never committed.
    """
    page = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    page = page.replace("__BRAINY_GATEWAY_TOKEN__", json.dumps(_load_or_create_gateway_token()))
    return HTMLResponse(page)


app.include_router(v1)
