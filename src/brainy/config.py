"""Central configuration, loaded from environment / .env via pydantic-settings.

All persisted data lives under one absolute root. Historically the db/chroma/workspace/
voice paths were each their own CWD-relative field ("./data/..."), which meant the exact
same code produced a different store depending on which directory it was launched from -
the direct cause of three diverged SQLite DBs and three diverged Chroma dirs. They are
now read-only properties derived from a single root, not independently settable fields,
so there is no way to reintroduce the divergence. `.env` may still carry the old
`brainy_DATA_DIR=./data`-style keys from before this change; `extra="ignore"`
means they are silently ignored rather than reintroducing CWD-relative paths.

Root resolution priority (see `Settings.data_root`):
    1. `BRAINY_DATA_DIR` (current, preferred env var)
    2. `NEXUS_DATA_DIR` (legacy name, still honored)
    3. `~/.brainy/data` (cross-platform default - no more machine-specific paths)
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _cross_platform_default_root() -> Path:
    """Cross-platform fallback used when neither BRAINY_DATA_DIR nor NEXUS_DATA_DIR
    is set. Replaces the previous hardcoded, machine-specific Windows path."""
    return Path.home() / ".brainy" / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 90.0
    # Tuned for responsive CPU-only local inference. Override in .env for longer answers.
    # Keep interactive chat responsive on CPU-only laptops. These remain
    # configurable through .env for users who prefer longer answers.
    ollama_max_tokens: int = 64
    ollama_num_ctx: int = 2048
    ollama_num_thread: int = 0
    ollama_keep_alive: str = "30m"

    embedding_model: str = "all-MiniLM-L6-v2"

    # Single root every data path derives from.
    # Preferred env var: BRAINY_DATA_DIR. Legacy env var: NEXUS_DATA_DIR (still
    # honored so existing .env files keep working). Must be absolute if set at
    # all - see _require_absolute below.
    brainy_data_dir_override: str | None = Field(default=None, validation_alias="BRAINY_DATA_DIR")
    nexus_data_dir: str | None = None

    night_shift_log_path: str = "../NIGHT_SHIFT.md"

    retrieval_top_k: int = 2
    rag_context_max_chars: int = 1200
    retrieval_min_similarity: float = 0.25
    memory_recency_half_life_days: float = 30.0
    memory_score_relevance_weight: float = 0.60
    memory_score_importance_weight: float = 0.15
    memory_score_recency_weight: float = 0.15
    memory_score_frequency_weight: float = 0.04
    memory_score_confidence_weight: float = 0.03
    memory_score_source_reliability_weight: float = 0.02
    memory_score_user_interaction_weight: float = 0.01
    memory_decay_after_days: float = 14.0
    memory_decay_multiplier: float = 0.90
    memory_archive_importance_floor: float = 0.05
    memory_archive_after_days: float = 90.0

    agent_max_steps: int = 6
    whisper_model_size: str = "base"

    @field_validator("brainy_data_dir_override", "nexus_data_dir")
    @classmethod
    def _require_absolute(cls, value: str | None, info) -> str | None:
        if value is not None and not Path(value).is_absolute():
            env_name = "BRAINY_DATA_DIR" if info.field_name == "brainy_data_dir_override" else "NEXUS_DATA_DIR"
            raise ValueError(f"{env_name} must be an absolute path, got {value!r}.")
        return value

    @property
    def data_root(self) -> Path:
        if self.brainy_data_dir_override:
            return Path(self.brainy_data_dir_override)
        if self.nexus_data_dir:
            return Path(self.nexus_data_dir)
        return _cross_platform_default_root()

    @property
    def brainy_data_dir(self) -> str:
        return str(self.data_root)

    @property
    def brainy_db_path(self) -> str:
        return str(self.data_root / "brainy.db")

    @property
    def brainy_chroma_dir(self) -> str:
        return str(self.data_root / "chroma")

    @property
    def brainy_workspace_dir(self) -> str:
        return str(self.data_root / "workspace")

    @property
    def brainy_voice_dir(self) -> str:
        return str(self.data_root / "voice")

    @property
    def brainy_gateway_token_path(self) -> str:
        return str(self.data_root / "gateway_token")

    def ensure_data_dirs(self) -> None:
        Path(self.brainy_data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.brainy_chroma_dir).mkdir(parents=True, exist_ok=True)
        Path(self.brainy_db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.brainy_workspace_dir).mkdir(parents=True, exist_ok=True)
        Path(self.brainy_voice_dir).mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_data_dirs()
    return _settings


def reset_settings() -> None:
    """Clear the cached singleton so a changed NEXUS_DATA_DIR (or other env var) takes
    effect on the next `get_settings()` call. Test-only - production code never needs
    to reload settings mid-process."""
    global _settings
    _settings = None
