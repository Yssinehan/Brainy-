# Brainy web interface

The browser interface lives in `src/brainy/interfaces/web/` and is deliberately plain
HTML, CSS, and JavaScript: no separate Node build, server, or dependency is required.

Run the API from the repository root:

```powershell
& "venv\Scripts\python" -m uvicorn brainy.interfaces.api:app --reload
```

Then open `http://127.0.0.1:8000`. The UI is served by FastAPI at `/`; assets are under
`/ui/`. It exposes only the core working modes: grounded chat, agent runs, browser audio,
image description/ingestion, and a secondary text-ingestion panel.

## Local security choice

The API gateway token remains mandatory for every API endpoint. FastAPI injects the
per-install token into the HTML page it serves locally, rather than exposing a token
endpoint or asking users to copy `data/gateway_token`. The middleware permits an `Origin`
header only if it exactly matches the current request's scheme and host; all external
origins remain blocked. Static assets and the initial page are public solely so the local
browser can bootstrap, and are not API operations.

`/voice/ask` additionally returns `transcript` alongside the normal `Answer` fields so
the interface can show what it heard without transcribing the recording twice. The RAG
pipeline remains unchanged. Spoken answers use the browser's `speechSynthesis` API.
