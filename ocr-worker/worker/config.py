"""Worker configuration: plain environment variables, no pydantic-settings.

ocr-worker is a standalone project (does not import `backend/app`), so it keeps its own
minimal config rather than pulling in pydantic-settings for four values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    database_url: str
    app_data_dir: Path
    poll_interval_s: float
    stale_job_minutes: int

    @property
    def documents_dir(self) -> Path:
        return self.app_data_dir / "documents"


def load_config() -> Config:
    return Config(
        database_url=os.environ["DATABASE_URL"],
        app_data_dir=Path(os.environ.get("APP_DATA_DIR", "/data")),
        poll_interval_s=float(os.environ.get("POLL_INTERVAL_S", "2")),
        stale_job_minutes=int(os.environ.get("STALE_JOB_MINUTES", "10")),
    )
