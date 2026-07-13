"""
core/config.py
================
Centralized, typed application configuration.

Every environment variable the backend reads (see `.env.example` at the repo
root for the full annotated reference) is declared here as a typed Pydantic
`Settings` field. This gives us three guarantees other backends often lack:

1. **Fail-fast validation** — a malformed `DATABASE_URL` or out-of-range port
   raises a clear error at startup instead of a confusing runtime failure.
2. **Single source of truth** — every other module imports `settings` from
   here rather than calling `os.environ.get(...)` ad hoc, so there's exactly
   one place that knows how configuration is sourced.
3. **Safe-by-default mock mode** — when `GEMINI_API_KEY` / `SERPAPI_KEY` are
   left blank (the default in `.env.example`), `settings.llm_mode` and
   `settings.search_mode` resolve to "mock", and every agent in the system
   transparently swaps in deterministic mock providers (see
   `app/tools/llm.py` and `app/tools/search.py`). This is what lets the
   ENTIRE multi-agent platform run end-to-end with zero API cost and zero
   external dependencies — exactly what was requested for local development
   without API keys.
"""

from functools import lru_cache
from typing import Literal

from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The backend/ directory — used to resolve relative paths deterministically
# regardless of the working directory uvicorn is started from.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    """Typed application settings, populated from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    app_name: str = Field(default="careerkundi-backend")
    app_version: str = Field(default="0.1.0")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_secret_key: str = Field(default="dev-only-insecure-secret-change-me")

    # --- LLM providers ---------------------------------------------------------
    gemini_api_key: str = Field(default="")
    # Use the "-latest" aliases rather than pinned dated versions: Google returns
    # 404 "no longer available to new users" for specific old IDs (e.g.
    # gemini-2.5-flash) on newly-issued keys, whereas the -latest aliases always
    # resolve to a currently-served model.
    gemini_model_flash: str = Field(default="gemini-flash-latest")
    gemini_model_pro: str = Field(default="gemini-pro-latest")
    gemini_embedding_model: str = Field(default="text-embedding-004")
    serpapi_key: str = Field(default="")

    # --- LLM backend selection -------------------------------------------------
    # "auto"   → gemini if GEMINI_API_KEY is set, else mock (original behavior).
    # "gemini" → force the live Gemini provider.
    # "ollama" → use a local Ollama server (free, no quota) — for testing.
    # "mock"   → force the deterministic offline provider.
    llm_provider: Literal["auto", "gemini", "ollama", "mock"] = Field(default="auto")
    # Base URL of the Ollama server. From inside Docker use host.docker.internal;
    # from the host directly use http://localhost:11434.
    ollama_base_url: str = Field(default="http://host.docker.internal:11434")
    ollama_model: str = Field(default="llama3.1:8b")

    # --- Database ---------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://careerkundi:careerkundi@localhost:5432/careerkundi"
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://careerkundi:careerkundi@localhost:5432/careerkundi"
    )

    # --- Cache ---------------------------------------------------------------------
    redis_url: str = Field(default="redis://localhost:6379/0")

    # --- Vector store / knowledge graph (RAG + GraphRAG) ----------------------------
    # These paths are resolved relative to the backend/ directory (not CWD)
    # so they work identically whether you start uvicorn from backend/ or from /.
    vector_store_url: str = Field(default="")
    vector_store_provider: Literal["faiss", "pinecone", "weaviate"] = Field(default="faiss")
    graph_store_path: str = Field(default="")
    documents_root: str = Field(default="", description="Project documents/ folder for role-pack PDF library")

    @property
    def resolved_documents_root(self) -> str:
        """Absolute path to documents/ (role-pack PDF library + indexes)."""
        if self.documents_root:
            return str(Path(self.documents_root).resolve())
        return str(_PROJECT_ROOT / "documents")

    @property
    def resolved_vector_store_path(self) -> str:
        """Absolute path to the FAISS vector store directory."""
        if self.vector_store_url:
            return str(Path(self.vector_store_url).resolve())
        return str(_BACKEND_ROOT / "data" / "vector_store")

    @property
    def resolved_graph_store_path(self) -> str:
        """Absolute path to the knowledge graph pickle file."""
        if self.graph_store_path:
            return str(Path(self.graph_store_path).resolve())
        return str(_BACKEND_ROOT / "data" / "knowledge_graph.gpickle")

    # --- Auth ------------------------------------------------------------------------
    jwt_secret: str = Field(default="dev-only-insecure-jwt-secret-change-me")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # --- CORS --------------------------------------------------------------------------
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    # --- Web scraping ------------------------------------------------------------------
    playwright_browser: Literal["chromium", "firefox", "webkit"] = Field(default="chromium")
    scraper_user_agent: str = Field(
        default="CareerkundiBot/1.0 (+https://careerkundi.com/bot)"
    )
    scraper_timeout_ms: int = Field(default=15000)
    scraper_max_concurrency: int = Field(default=4)

    # --- Rate limiting -------------------------------------------------------------------
    rate_limit_unauthenticated: str = Field(default="30/minute")
    rate_limit_authenticated: str = Field(default="120/minute")
    rate_limit_llm_heavy: str = Field(default="10/minute")

    # --- Cost controls --------------------------------------------------------------------
    token_budget_per_request: int = Field(default=200_000)
    prompt_cache_ttl_seconds: int = Field(default=86_400)

    # --- Job search study synthesis -------------------------------------------------------
    job_search_enable_model_knowledge: bool = Field(
        default=False,
        description="Enable model-knowledge study synthesis (disabled by default; no API calls unless provider configured).",
    )
    job_search_model_knowledge_provider: Literal["disabled", "deterministic_test", "gemini"] = Field(
        default="disabled",
        description="Model-knowledge provider: disabled | deterministic_test (tests/samples) | gemini (future).",
    )

    # --- Observability ----------------------------------------------------------------------
    otel_exporter_otlp_endpoint: str = Field(default="")
    log_level: str = Field(default="INFO")

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors(cls, v: str) -> str:
        """Ensure CORS origins is a non-empty comma-separated string."""
        return v or "http://localhost:5173"

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        """
        SECURITY GUARD: refuse to start the server if insecure default
        secrets are used outside of development mode. This prevents
        accidental deployment with the demo secrets from .env.example.
        """
        if self.app_env in ("staging", "production"):
            for field_name, value in [
                ("app_secret_key", self.app_secret_key),
                ("jwt_secret", self.jwt_secret),
            ]:
                if "change-me" in value or "insecure" in value:
                    raise ValueError(
                        f"FATAL: {field_name} contains an insecure default value. "
                        f"Set a real secret in .env before running in {self.app_env} mode."
                    )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Split the comma-separated CORS_ORIGINS env var into a clean list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_llm_provider(self) -> Literal["gemini", "ollama", "mock"]:
        """
        The concrete LLM backend to use, resolving the "auto" default. An
        explicit `LLM_PROVIDER` wins; otherwise we use Gemini when an API key
        is present and fall back to the deterministic mock provider.
        """
        p = (self.llm_provider or "auto").strip().lower()
        if p in ("gemini", "ollama", "mock"):
            return p  # explicit override
        return "gemini" if self.gemini_api_key.strip() else "mock"

    @property
    def llm_mode(self) -> Literal["live", "mock"]:
        """
        "live" means "call a real LLM" (Gemini OR a local Ollama model);
        "mock" means the deterministic offline provider. Kept as a two-value
        property because the whole pipeline branches on it — a real local
        model is still a live path (so LLM-authored content is preserved
        rather than overwritten by the template engine).
        """
        return "mock" if self.resolved_llm_provider == "mock" else "live"

    @property
    def search_mode(self) -> Literal["live", "mock"]:
        """Decide whether grounding agents hit real SerpAPI or canned mock search results."""
        return "live" if self.serpapi_key.strip() else "mock"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton `Settings` instance.

    `lru_cache` ensures the `.env` file is parsed exactly once per process,
    which matters because every agent, route, and background task imports
    this function rather than instantiating `Settings()` directly.
    """
    return Settings()


# Module-level singleton imported throughout the codebase as `from app.core.config import settings`.
settings = get_settings()
