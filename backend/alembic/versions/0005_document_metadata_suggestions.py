"""document_metadata_suggestions (Phase 3.2, SPEC_02 §4)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUGGESTION_STATUS = postgresql.ENUM(
    "pending", "applied", "rejected", "failed", name="suggestion_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE TYPE suggestion_status AS ENUM ('pending', 'applied', 'rejected', 'failed')")

    op.create_table(
        "document_metadata_suggestions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("status", SUGGESTION_STATUS, nullable=False, server_default="pending"),
        sa.Column("fields", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applied_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("document_id", name="uq_document_metadata_suggestions_document_id"),
    )

    # `documents.ai_suggestion_id` deliberately stays FK-less: a real FK here would form a
    # cycle with `document_metadata_suggestions.document_id -> documents.id` (SQLAlchemy
    # cannot topologically sort the two tables, and Postgres tolerates it but every ORM
    # tool that walks FKs has to special-case it). The column is kept in sync by
    # `app/services/metadata_suggestion.py` only, purely as an existence flag ("has this
    # document had a suggestion attempt") — lookups always go through
    # `document_metadata_suggestions.document_id`, never through this column.


def downgrade() -> None:
    op.drop_table("document_metadata_suggestions")
    op.execute("DROP TYPE suggestion_status")
