"""Shared fixtures. Tests run only against the separate `company_ai_test` database
(mirrors backend's `tests/conftest.py` safety check)."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, make_url, text

from worker.config import Config
from worker.db import Tables, make_engine


@pytest.fixture(scope="session")
def database_url() -> str:
    import os

    url = os.environ["DATABASE_URL"]
    parsed = make_url(url)
    assert parsed.database and parsed.database.endswith("_test"), (
        f"refusing to run tests against non-test database {parsed.database!r}; "
        "set DATABASE_URL to the *_test database"
    )
    return url


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    eng = make_engine(database_url)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def tables(engine: Engine) -> Tables:
    return Tables(engine)


@pytest.fixture
def _clean_tables(engine: Engine) -> Iterator[None]:
    """Not autouse: only `test_pipeline.py` needs (or can afford) a live database —
    `test_chunking.py`/`test_image_to_pdf.py` must run with no `DATABASE_URL` set at all.
    `test_pipeline.py` opts in via `pytestmark = pytest.mark.usefixtures("_clean_tables")`.
    """
    yield
    with engine.begin() as conn:
        for table_name in ("ingestion_jobs", "document_chunks", "document_pages", "documents"):
            conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))


@pytest.fixture
def app_data_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "documents").mkdir(parents=True, exist_ok=True)
        yield path


@pytest.fixture
def config(database_url: str, app_data_dir: Path) -> Config:
    return Config(
        database_url=database_url,
        app_data_dir=app_data_dir,
        poll_interval_s=0.1,
        stale_job_minutes=10,
    )
