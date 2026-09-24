"""audit_log (Phase 3.4, SPEC_06 §1)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        # FK + SET NULL, same as documents.uploaded_by_id — the row survives a deleted
        # user, only the pointer clears.
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("question", sa.Text(), nullable=False),
        # Router (ADR-010) lands in Phase 4.3; every row is "DOCUMENT_QUERY" until then.
        sa.Column(
            "query_type", sa.String(32), nullable=False, server_default="DOCUMENT_QUERY"
        ),
        sa.Column("scope_department", sa.String(128), nullable=True),
        sa.Column("scope_project", sa.Uuid(), nullable=True),
        sa.Column(
            "documents_retrieved", postgresql.ARRAY(sa.Uuid()), nullable=False, server_default="{}"
        ),
        # Phase 4.2 (Excel engine) is the only future writer of this; always [] until then.
        sa.Column(
            "excel_files_used", postgresql.ARRAY(sa.String(255)), nullable=False, server_default="{}"
        ),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        # USD; NULL when the model has no known price (never a guessed number).
        sa.Column("cost_estimate", sa.Numeric(10, 6), nullable=True),
        sa.Column("execution_ms", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        # scope_project/documents_retrieved deliberately carry no FK: an audit row must
        # survive the deletion of a project or document it references (same reasoning as
        # `documents.related_document_ids`, which is also FK-less).
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_user_id_timestamp", "audit_log", ["user_id", "timestamp"])


def downgrade() -> None:
    op.drop_table("audit_log")
