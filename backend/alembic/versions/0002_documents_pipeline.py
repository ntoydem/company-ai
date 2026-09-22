"""documents pipeline: documents, document_pages, document_chunks, ingestion_jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DOCUMENT_STATUS = postgresql.ENUM(
    "draft",
    "executed",
    "amended",
    "superseded",
    "active",
    name="document_status",
    create_type=False,
)
CONFIDENTIALITY_LEVEL = postgresql.ENUM(
    "normal", "restricted", "board", name="confidentiality_level", create_type=False
)
DOCUMENT_SOURCE = postgresql.ENUM("web", "consume", name="document_source", create_type=False)
INGESTION_STATUS = postgresql.ENUM(
    "uploaded", "ocr", "ready", "failed", name="ingestion_status", create_type=False
)
INGESTION_JOB_STATUS = postgresql.ENUM(
    "queued", "running", "done", "failed", name="ingestion_job_status", create_type=False
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE document_status AS ENUM "
        "('draft', 'executed', 'amended', 'superseded', 'active')"
    )
    op.execute("CREATE TYPE confidentiality_level AS ENUM ('normal', 'restricted', 'board')")
    op.execute("CREATE TYPE document_source AS ENUM ('web', 'consume')")
    op.execute("CREATE TYPE ingestion_status AS ENUM ('uploaded', 'ocr', 'ready', 'failed')")
    op.execute(
        "CREATE TYPE ingestion_job_status AS ENUM ('queued', 'running', 'done', 'failed')"
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Mandatory (SPEC_02 §2)
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("subdepartment", sa.String(128), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=False),
        sa.Column("status", DOCUMENT_STATUS, nullable=False, server_default="draft"),
        sa.Column(
            "confidentiality", CONFIDENTIALITY_LEVEL, nullable=False, server_default="normal"
        ),
        sa.Column("tags", postgresql.ARRAY(sa.String(64)), nullable=False, server_default="{}"),
        sa.Column("source", DOCUMENT_SOURCE, nullable=False, server_default="web"),
        # Temporal (ADR-012)
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supersedes_document_id", sa.Uuid(), nullable=True),
        sa.Column("superseded_by_document_id", sa.Uuid(), nullable=True),
        sa.Column(
            "related_document_ids", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"
        ),
        # System
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("ingestion_status", INGESTION_STATUS, nullable=False, server_default="uploaded"),
        sa.Column("ingestion_error", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=True),
        sa.Column("ai_suggestion_id", sa.Uuid(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["supersedes_document_id"], ["documents.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_document_id"], ["documents.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_documents_department", "documents", ["department"])
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_ingestion_status", "documents", ["ingestion_status"])

    op.create_table(
        "document_pages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "document_id", "page_number", name="uq_document_pages_document_page"
        ),
    )
    op.create_index("ix_document_pages_document_id", "document_pages", ["document_id"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "tsv_turkish",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('turkish', text)", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "tsv_simple",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', text)", persisted=True),
            nullable=False,
        ),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_chunk_index"
        ),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index(
        "ix_document_chunks_tsv_turkish",
        "document_chunks",
        ["tsv_turkish"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_document_chunks_tsv_simple",
        "document_chunks",
        ["tsv_simple"],
        postgresql_using="gin",
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("status", INGESTION_JOB_STATUS, nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ingestion_jobs_document_id", "ingestion_jobs", ["document_id"])
    op.create_index(
        "ix_ingestion_jobs_status_created_at", "ingestion_jobs", ["status", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_jobs_status_created_at", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_document_id", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")

    op.drop_index("ix_document_chunks_tsv_simple", table_name="document_chunks")
    op.drop_index("ix_document_chunks_tsv_turkish", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_document_pages_document_id", table_name="document_pages")
    op.drop_table("document_pages")

    op.drop_index("ix_documents_ingestion_status", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_index("ix_documents_department", table_name="documents")
    op.drop_table("documents")

    op.execute("DROP TYPE ingestion_job_status")
    op.execute("DROP TYPE ingestion_status")
    op.execute("DROP TYPE document_source")
    op.execute("DROP TYPE confidentiality_level")
    op.execute("DROP TYPE document_status")
