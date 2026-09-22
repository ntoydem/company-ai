"""Engine + reflected table handles.

Backend's Alembic migration is the single source of truth for the schema (ADR-002); this
worker never defines tables itself, it reflects them at startup. If a migration renames or
drops a column this worker expects, reflection succeeds but the missing attribute access
fails loudly (AttributeError / KeyError) rather than silently drifting.
"""

from __future__ import annotations

from sqlalchemy import Engine, MetaData, Table, create_engine

REFLECTED_TABLES = ("documents", "document_pages", "document_chunks", "ingestion_jobs")


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


class Tables:
    def __init__(self, engine: Engine) -> None:
        metadata = MetaData()
        metadata.reflect(bind=engine, only=REFLECTED_TABLES)
        self.documents: Table = metadata.tables["documents"]
        self.document_pages: Table = metadata.tables["document_pages"]
        self.document_chunks: Table = metadata.tables["document_chunks"]
        self.ingestion_jobs: Table = metadata.tables["ingestion_jobs"]
