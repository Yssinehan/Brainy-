"""FastAPI surface - the stable HTTP API non-Python callers use (docs/TDD.md section 8)."""

from __future__ import annotations

import json
import logging
import re
import secrets
import sqlite3
import tempfile
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from brainy import __version__
from brainy.errors import BrainyError
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
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
WEB_DIR = Path(__file__).with_name("web")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
app.mount("/ui", StaticFiles(directory=WEB_DIR), name="brainy-ui")


@app.on_event("startup")
def warm_local_models() -> None:
    """Remove the Ollama cold-load penalty from the first user-visible response."""
    try:
        build_engine().router.warmup()
        log.info("[PERF] Ollama warmup complete")
    except RouterError as exc:
        log.warning("[PERF] Ollama warmup skipped: %s", exc)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Trop de requetes, reessayez dans une minute."})
v1 = APIRouter(prefix="/api/v1")


@app.exception_handler(BrainyError)
async def _brainy_error_handler(request: Request, exc: BrainyError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": exc.error_code, "message": exc.message, "details": exc.details},
    )


@app.exception_handler(BrainyError)
async def _brainy_error_handler(request: Request, exc: BrainyError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": exc.error_code, "message": exc.message, "details": exc.details},
    )

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
    """Protect API calls while allowing an unauthenticated health check."""
    # The local web application and its static assets must load before they can
    # make authenticated, same-origin API requests.
    if request.url.path in {"/", "/health"} or request.url.path.startswith("/ui/"):
        return await call_next(request)

    origin = request.headers.get("origin")
    expected_origin = f"{request.url.scheme}://{request.headers.get('host', '')}"
    if origin and not secrets.compare_digest(origin.rstrip("/"), expected_origin.rstrip("/")):
        return JSONResponse(status_code=403, content={"detail": "Cross-origin requests are not allowed."})
    if request.headers.get(GATEWAY_TOKEN_HEADER) != _load_or_create_gateway_token():
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid X-DreamOS-Token."})
    return await call_next(request)


async def _read_upload(upload: UploadFile) -> bytes:
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Le fichier est vide.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 10 Mo.")
    return content


async def _save_upload_to_temp(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await _read_upload(upload))
        return tmp.name


def _ai() -> PersonalAIEngine:
    return PersonalAIEngine(build_engine())


def _require_ollama(engine: PersonalAIEngine) -> None:
    """Fail fast instead of loading embeddings when the required chat model is down."""
    if not engine.router.provider_status().get("ollama", False):
        settings = get_settings()
        raise RouterError(
            f"Ollama est indisponible sur {settings.ollama_host}. "
            f"Démarrez Ollama puis téléchargez le modèle {settings.ollama_model}."
        )


def _user_error(detail: object) -> str:
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            location = " ".join(str(part) for part in first.get("loc", ()) if part != "body")
            message = first.get("msg", "RequÃªte invalide.")
            return f"{location}: {message}" if location else message
        return str(first)
    return "La requÃªte nâ€™a pas pu Ãªtre traitÃ©e."


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


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2_000)


class ChatRequest(BaseModel):
    message: str
    k: int | None = None
    verify: bool = False
    history: list[ConversationMessage] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: list[Source]
    memory_used: bool
    grounded: bool
    disagreement: bool = False
    text: str
    event: dict | None = None


class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    start: str
    end: str | None = None
    description: str = ""
    location: str = ""
    reminder: str = "30 minutes avant"
    recurrence: str = ""
    category: str = "Personnel"
    conversation_id: str | None = None
    source_type: str = "manual"
    source_id: str | None = None
    source_label: str = "Créé manuellement"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class EventExtraction(BaseModel):
    """The validated, transport-neutral shape produced by the event pipeline."""

    title: str
    date: str
    time: str | None = None
    end_time: str | None = None
    location: str | None = None
    description: str | None = None
    source: str


_EVENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  start TEXT NOT NULL,
  end_time TEXT,
  description TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL DEFAULT '',
  reminder TEXT NOT NULL DEFAULT '30 minutes avant',
  recurrence TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT 'Personnel',
  conversation_id TEXT,
  source_type TEXT NOT NULL DEFAULT 'manual',
  source_id TEXT,
  source_label TEXT NOT NULL DEFAULT 'Créé manuellement',
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_title_start ON events(title COLLATE NOCASE, start);
"""


def _events_path() -> Path:
    """Legacy JSON path, kept only to migrate existing local calendar entries once."""
    return Path(get_settings().brainy_data_dir) / "calendar_events.json"


def _events_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_settings().brainy_db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_EVENT_SCHEMA)
    return conn


def _migrate_legacy_events(conn: sqlite3.Connection) -> None:
    """Import the previous JSON calendar without losing a user's existing events."""
    if conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] or not _events_path().exists():
        return
    try:
        legacy = json.loads(_events_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for item in legacy if isinstance(legacy, list) else []:
        try:
            event = CalendarEvent.model_validate(item)
            _insert_event(conn, event)
        except Exception:
            log.warning("Skipping invalid legacy calendar event during SQLite migration")


def _read_events() -> list[dict]:
    with _events_connection() as conn:
        _migrate_legacy_events(conn)
        return [dict(row) for row in conn.execute(
            "SELECT id, title, start, end_time AS end, description, location, reminder, recurrence, category, "
            "conversation_id, source_type, source_id, source_label, created_at FROM events ORDER BY start, created_at"
        )]


def _write_events(events: list[dict]) -> None:
    """Compatibility writer for callers which replace the complete event collection."""
    with _events_connection() as conn:
        conn.execute("DELETE FROM events")
        for item in events:
            _insert_event(conn, CalendarEvent.model_validate(item))


def _insert_event(conn: sqlite3.Connection, event: CalendarEvent) -> bool:
    values = event.model_dump()
    cursor = conn.execute(
        """INSERT OR IGNORE INTO events
           (id, title, start, end_time, description, location, reminder, recurrence,
            category, conversation_id, source_type, source_id, source_label, created_at)
           VALUES (:id, :title, :start, :end, :description, :location, :reminder, :recurrence,
                   :category, :conversation_id, :source_type, :source_id, :source_label, :created_at)""",
        values,
    )
    return cursor.rowcount == 1


def _save_event(event: CalendarEvent) -> tuple[CalendarEvent, bool]:
    """Persist an event once. Equality is title + precise date/time, across imports."""
    with _events_connection() as conn:
        _migrate_legacy_events(conn)
        if _insert_event(conn, event):
            return event, True
        row = conn.execute(
            "SELECT id, title, start, end_time AS end, description, location, reminder, recurrence, category, "
            "conversation_id, source_type, source_id, source_label, created_at FROM events "
            "WHERE title = ? COLLATE NOCASE AND start = ?", (event.title, event.start)
        ).fetchone()
        return CalendarEvent.model_validate(dict(row)), False


def _record_document(name: str, conversation_id: str | None, status: str) -> None:
    """Keep attachment metadata alongside the memory index for conversation continuity."""
    path = Path(get_settings().brainy_data_dir) / "conversation_documents.json"
    try:
        records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except (json.JSONDecodeError, OSError):
        records = []
    records.append({"name": name, "conversation_id": conversation_id, "status": status, "imported_at": datetime.now().isoformat()})
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


_MONTHS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
           "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
           "décembre": 12, "decembre": 12}
_EVENT_WORDS = ("examen", "réunion", "reunion", "rendez-vous", "rendez vous", "cours", "formation",
                "présentation", "presentation", "soutenance", "deadline", "date limite", "rendu",
                "événement", "evenement", "conférence", "conference", "atelier", "meeting", "rappel")
_DATE_RE = re.compile(r"\b(?:(\d{4})-(\d{1,2})-(\d{1,2})|(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?|(\d{1,2})\s+(%s)(?:\s+(\d{4}))?)\b" % "|".join(_MONTHS), re.I)
_TIME_RE = re.compile(r"(?:\b(?:à|a|heure)\s*:?\s*)?(\d{1,2})(?:\s*h\s*|:)(\d{2})?\b", re.I)


def _normalise_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n").replace("\\*", "\n*")
    # OCR may preserve Markdown-like bullets ("* **Date :** …").
    # Remove presentation markup before interpreting their labels.
    text = re.sub(r"(?m)^\s*[-*•]\s*", "", text)
    return text.replace("**", "")


def _date_from_match(match: re.Match[str]) -> str | None:
    try:
        if match.group(1):
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        elif match.group(4):
            day, month, raw_year = int(match.group(4)), int(match.group(5)), match.group(6)
            year = int(raw_year) if raw_year and len(raw_year) == 4 else (2000 + int(raw_year) if raw_year else datetime.now().year)
        else:
            day, month, raw_year = int(match.group(7)), _MONTHS[match.group(8).lower()], match.group(9)
            year = int(raw_year) if raw_year else datetime.now().year
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def _event_category(title: str) -> str:
    text = title.lower()
    if "examen" in text or "soutenance" in text:
        return "Examen"
    if any(word in text for word in ("rendu", "deadline", "date limite", "devoir")):
        return "Devoir"
    if any(word in text for word in ("cours", "formation", "atelier")):
        return "Cours"
    return "Personnel"


def _clean_title(value: str) -> str:
    value = re.sub(r"\b(?:date|heure|lieu|sujet|objet|description)\s*:\s*", "", value, flags=re.I)
    value = _DATE_RE.sub("", value)
    value = _TIME_RE.sub("", value)
    value = re.sub(r"\b(?:le|à|a)\s*$", "", value, flags=re.I)
    return re.sub(r"\s{2,}", " ", value).strip(" -:,.\t")


def _label_value(text: str, labels: str) -> str | None:
    match = re.search(rf"\b(?:{labels})\s*:\s*([^\n|]+)", text, re.I)
    return match.group(1).strip(" -–—:\t") if match else None


def _extract_events(text: str, source: str) -> list[EventExtraction]:
    """Extract validated event JSON records without treating an isolated date as an event.

    This deterministic parser is deliberately used before any optional LLM: uploads stay
    useful offline, responses are already structured, and malformed model output cannot
    break ingestion.
    """
    text = _normalise_text(text)
    lines = [line.strip() for line in text.split("\n")]
    found: list[EventExtraction] = []
    for index, line in enumerate(lines):
        match = _DATE_RE.search(line)
        if not match:
            continue
        date = _date_from_match(match)
        if not date:
            continue
        nearby = " ".join(lines[max(0, index - 2):min(len(lines), index + 4)])
        # A precise date alone (e.g. a document creation date) is never enough.
        if not any(word in nearby.lower() for word in _EVENT_WORDS) and not re.search(r"\b(date|heure|lieu|sujet)\s*:", nearby, re.I):
            continue
        candidate = _clean_title(line[:match.start()] + line[match.end():])
        if not candidate or candidate.lower() in {"date", "le"}:
            previous = next((lines[p] for p in range(index - 1, max(-1, index - 4), -1) if lines[p]), "")
            candidate = _clean_title(previous)
        if not candidate:
            keyword = next((word for word in _EVENT_WORDS if word in nearby.lower()), None)
            candidate = keyword.title() if keyword else "Événement"
        # Conversational wording ("j'ai une soutenance ...") is not a useful
        # calendar title; retain the explicit event phrase instead.
        keyword_match = re.search(r"\b(" + "|".join(re.escape(word) for word in _EVENT_WORDS) + r")\b.*", candidate, re.I)
        if keyword_match:
            candidate = keyword_match.group(0).strip(" -:,")
        time_match = _TIME_RE.search(line[match.end():]) or re.search(r"\bheure\s*:\s*(\d{1,2})(?:\s*h\s*|:)(\d{2})?", nearby, re.I)
        time = None
        if time_match:
            hour, minute = int(time_match.group(1)), int(time_match.group(2) or 0)
            if hour < 24 and minute < 60:
                time = f"{hour:02d}:{minute:02d}"
        fields = "\n".join(lines[max(0, index - 2):index + 4])
        location = _label_value(fields, "lieu")
        subject = _label_value(fields, "sujet|description|objet")
        # A labelled subject often contains "Titre – description". Keep these
        # separately so neither the calendar title nor the description is noisy.
        if subject and (candidate.lower() in {"réunion", "reunion", "événement", "evenement"}):
            parts = re.split(r"\s+[–—-]\s+", subject, maxsplit=1)
            candidate = parts[0].strip()
            if len(parts) == 2:
                subject = parts[1].strip()
        found.append(EventExtraction(title=candidate, date=date, time=time,
                                     location=location,
                                     description=subject or candidate,
                                     source=source))
    unique: dict[tuple[str, str, str | None], EventExtraction] = {}
    for event in found:
        unique[(event.title.casefold(), event.date, event.time)] = event
    return list(unique.values())


def _calendar_event(extracted: EventExtraction, *, conversation_id: str | None = None,
                    source_id: str | None = None, source_label: str = "Chat") -> CalendarEvent:
    # Midnight represents an all-day event; it is not a guessed appointment time.
    start = f"{extracted.date}T{extracted.time or '00:00'}:00"
    end = f"{extracted.date}T{extracted.end_time}:00" if extracted.end_time else None
    return CalendarEvent(title=extracted.title, start=start, end=end, location=extracted.location or "",
                         description=extracted.description or "", category=_event_category(extracted.title),
                         conversation_id=conversation_id, source_type=extracted.source, source_id=source_id,
                         source_label=source_label)


def _event_from_message(message: str, conversation_id: str | None = None, *, source_type: str = "chat",
                        source_id: str | None = None, source_label: str = "Chat") -> CalendarEvent | None:
    events = _extract_events(message, source_type)
    return _calendar_event(events[0], conversation_id=conversation_id, source_id=source_id, source_label=source_label) if events else None


def _store_extracted_events(text: str, source_type: str, *, conversation_id: str | None = None,
                            source_id: str | None = None, source_label: str) -> tuple[list[CalendarEvent], int]:
    saved: list[CalendarEvent] = []
    for extracted in _extract_events(text, source_type):
        event, created = _save_event(_calendar_event(extracted, conversation_id=conversation_id, source_id=source_id, source_label=source_label))
        if created:
            saved.append(event)
    return saved, len(_extract_events(text, source_type)) - len(saved)


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
    _require_ollama(engine)
    history = [Message(role=item.role, content=item.content) for item in req.history]
    answer = engine.process_message(req.message, k=req.k, verify=req.verify, history=history)
    response = _chat_response(answer, engine.conversation_id)
    event = _event_from_message(req.message, engine.conversation_id, source_id=engine.conversation_id)
    if event:
        event, _created = _save_event(event)
        response.event = event.model_dump()
    return response


@v1.get("/events", response_model=list[CalendarEvent])
def list_events() -> list[CalendarEvent]:
    return [CalendarEvent.model_validate(item) for item in _read_events()]


@v1.post("/events", response_model=CalendarEvent)
def create_event(event: CalendarEvent) -> CalendarEvent:
    if event.source_type == "manual" and event.source_label == "Créé manuellement":
        event.source_label = "Créé manuellement"
    return _save_event(event)[0]


@v1.put("/events/{event_id}", response_model=CalendarEvent)
def update_event(event_id: str, event: CalendarEvent) -> CalendarEvent:
    events = _read_events()
    for index, item in enumerate(events):
        if item.get("id") == event_id:
            event.id = event_id
            events[index] = event.model_dump()
            _write_events(events)
            return event
    raise HTTPException(status_code=404, detail="Événement introuvable.")


@v1.delete("/events/{event_id}")
def delete_event(event_id: str) -> dict:
    events = _read_events()
    remaining = [item for item in events if item.get("id") != event_id]
    if len(remaining) == len(events):
        raise HTTPException(status_code=404, detail="Événement introuvable.")
    _write_events(remaining)
    return {"deleted": event_id}


@v1.post("/documents")
async def upload_document(file: UploadFile = File(...), conversation_id: str | None = None) -> dict:
    """Extract supported text files and ingest them into the existing memory store."""
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()
    raw = await _read_upload(file)
    try:
        if suffix in {".txt", ".csv"}:
            text = raw.decode("utf-8", errors="replace")
        elif suffix == ".pdf":
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif suffix == ".docx":
            from docx import Document
            import io
            text = "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
        elif suffix == ".xlsx":
            import openpyxl
            import io
            book = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            text = "\n".join(" | ".join(str(cell) for cell in row if cell is not None) for sheet in book.worksheets for row in sheet.iter_rows(values_only=True))
        else:
            raise HTTPException(status_code=415, detail="Format non pris en charge. Utilisez PDF, DOCX, TXT, XLSX ou CSV.")
    except ImportError as exc:
        raise HTTPException(status_code=422, detail=f"L'import de {suffix} nécessite le module {exc.name}.")
    if not text.strip():
        raise HTTPException(status_code=422, detail="Aucun texte exploitable n’a été trouvé dans ce document.")
    result = _ai().ingest_text(text, doc_id=filename, source=filename)
    _record_document(filename, conversation_id, "analysé")
    events, duplicates = _store_extracted_events(text, "document", conversation_id=conversation_id,
                                                  source_id=filename, source_label=f"Document : {filename}")
    return {"name": filename, "conversation_id": conversation_id, "status": "analysé",
            "chunks_ingested": result.chunks_ingested, "event": events[0].model_dump() if events else None,
            "events": [event.model_dump() for event in events], "events_added": len(events),
            "events_already_exist": duplicates}


@v1.get("/documents")
def list_documents() -> list[dict]:
    path = Path(get_settings().brainy_data_dir) / "conversation_documents.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except (json.JSONDecodeError, OSError):
        return []


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


@app.post("/vision/ingest")
async def vision_ingest_endpoint(file: UploadFile = File(...), doc_id: str | None = None) -> dict:
    if Path(file.filename or "").suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=415, detail="Format image non pris en charge. Utilisez PNG, JPG ou WEBP.")
    tmp_path = await _save_upload_to_temp(file)
    try:
        from brainy.vision.ocr import extract_text_from_image

        text = extract_text_from_image(tmp_path)
    except VisionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    result = _ai().ingest_text(text, doc_id=doc_id or (file.filename or "image"), source=file.filename or "image")
    # Keep the established response fields while attaching calendar extraction data.
    events, duplicates = _store_extracted_events(text, "photo", source_id=file.filename or "image",
                                                  source_label=f"Image : {file.filename or 'image'}")
    return {**result.model_dump(), "event": events[0].model_dump() if events else None,
            "events": [event.model_dump() for event in events], "events_added": len(events),
            "events_already_exist": duplicates}


@app.get("/stats")
def stats_endpoint() -> dict:
    return _ai().stats()


@app.get("/health")
def health_endpoint() -> dict:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        local_ocr = True
    except Exception:
        local_ocr = False
    return {"status": "ok", "version": __version__, "local_ocr": local_ocr}


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
def web_interface() -> HTMLResponse:
    """Serve the local Brainy application and its same-origin gateway token."""
    page = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(page.replace("__BRAINY_GATEWAY_TOKEN__", json.dumps(_load_or_create_gateway_token())))


app.include_router(v1)
