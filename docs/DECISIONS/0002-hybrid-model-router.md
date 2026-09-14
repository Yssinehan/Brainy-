# ADR 0002: Ollama-only chat model router

**Status:** Accepted

**Context:** User wants privacy/offline capability where possible but needs strong reasoning quality and zero-cost operation today.

**Decision:** `ModelRouter` always uses a local embedding model (`sentence-transformers`) for `embed()`. For `complete()`, it health-checks the configured Ollama endpoint and uses it exclusively. It never falls back to Gemini, so chat prompts remain within the Ollama deployment.

**Consequences:** Ingest/retrieve work fully offline with no API key. Generation requires Ollama to be running and to contain the configured model. Gemini remains an opt-in dependency for the separate image-description endpoint only. Adding a third provider later is a new `Provider` class behind the same interface, but must not become an implicit chat fallback.
