"""Application settings. Single source: environment variables (loaded by compose from .env)."""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Company AI"
    app_env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: str
    # Container-side data root (host side is DATA_ROOT, used only by compose).
    app_data_dir: Path = Path("/data")

    # All "current / historical / which operating year" logic is relative to this date.
    demo_today: date = date(2026, 9, 15)

    admin_username: str = "admin"
    admin_password: SecretStr

    # Phase 1.1
    jwt_secret: SecretStr
    # Shared password for the four demo accounts (yonetim/finans/hukuk/enerji); they carry
    # no real access separation until Phase 1.2, so one shared password keeps demos simple.
    demo_user_password: SecretStr

    # Phase 0.3 (ADR-009)
    llm_provider: Literal["openai_compatible", "anthropic"] = "openai_compatible"
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_api_key: SecretStr | None = None
    llm_model_classify: str = "gemini-3.5-flash-lite"
    llm_model_answer: str = "gemini-3.8-flash"
    llm_timeout_s: int = 60
    llm_max_output_tokens: int = 2048
    # Thinking budget stays low (SPEC_01 §5); Gemini maps this to `thinking_level`.
    llm_reasoning_effort: Literal["minimal", "low", "medium", "high"] = "low"
    anthropic_api_key: SecretStr | None = None

    # Phase 3.4
    embeddings_enabled: bool = False
    embed_model_id: str = "BAAI/bge-m3"
    # Compose network hostname (service name `embed`); never reached when the flag above
    # is false — the client is built lazily, see app/services/embedding_client.py.
    embed_base_url: str = "http://embed:8080"
    embed_timeout_s: int = 30
    # Background backfill loop (app/main.py lifespan) — only starts when
    # embeddings_enabled=true and not against a `_test` database.
    embedding_backfill_interval_s: int = 15
    embedding_backfill_batch_size: int = 20

    # Phase 3.4: audit_log retention + cleanup (app/main.py lifespan).
    audit_log_retention_days: int = 90
    audit_log_cleanup_interval_s: int = 6 * 60 * 60

    # Phase 0.2
    max_upload_size_mb: int = 50
    # 40 (Phase 3.2b): a page-per-chunk corpus of ~450 chars/chunk makes 40 chunks ~10k
    # tokens — cheap for the answer model, and it clears the wide rank ties an OR query
    # produces (SORU 2, docs/plans/PHASE_3_2B_PLAN.md).
    retrieval_top_k: int = 40

    # Phase 3.2: background metadata-suggestion scan (app/main.py lifespan). Never runs
    # against a `_test` database (see `_background_enabled` there) — `make test` never
    # calls the LLM through this path.
    metadata_suggestion_poll_interval_s: int = 15
    metadata_suggestion_batch_size: int = 5

    @property
    def documents_dir(self) -> Path:
        return self.app_data_dir / "documents"

    @property
    def excel_dir(self) -> Path:
        return self.app_data_dir / "excel"

    @property
    def app_state_dir(self) -> Path:
        return self.app_data_dir / "app-data"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # required fields come from the environment
