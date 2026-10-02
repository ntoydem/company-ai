"""documents.review_status + review columns, document_review_events (B-28, ADR-024).

Every existing row becomes `approved` through the column DEFAULT (the 70 demo documents and
4 workbooks stay published — NOT §3.3); only `POST /api/documents/upload` creates pending
rows from here on. No data step needed.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REVIEW_STATUS = postgresql.ENUM(
    "pending_metadata",
    "pending_review",
    "changes_requested",
    "approved",
    name="document_review_status",
    create_type=False,
)
EVENT_KIND = postgresql.ENUM(
    "uploaded",
    "auto_approved",
    "field_edited",
    "field_confirmed",
    "submitted",
    "resubmitted",
    "approved",
    "changes_requested",
    "metadata_changed_after_approval",
    name="document_review_event_kind",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE document_review_status AS ENUM "
        "('pending_metadata', 'pending_review', 'changes_requested', 'approved')"
    )
    op.execute(
        "CREATE TYPE document_review_event_kind AS ENUM ('uploaded', 'auto_approved', "
        "'field_edited', 'field_confirmed', 'submitted', 'resubmitted', 'approved', "
        "'changes_requested', 'metadata_changed_after_approval')"
    )
    op.add_column(
        "documents",
        sa.Column("review_status", REVIEW_STATUS, nullable=False, server_default="approved"),
    )
    op.add_column("documents", sa.Column("review_comment", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("documents", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "reviewed_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_documents_review_status", "documents", ["review_status"])
    op.create_table(
        "document_review_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "actor_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("actor_name", sa.String(128), nullable=False),
        sa.Column("kind", EVENT_KIND, nullable=False),
        sa.Column("field", sa.String(64), nullable=True),
        sa.Column("before", sa.Text(), nullable=True),
        sa.Column("after", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_document_review_events_document_id_created_at",
        "document_review_events",
        ["document_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_review_events_document_id_created_at", table_name="document_review_events"
    )
    op.drop_table("document_review_events")
    op.drop_index("ix_documents_review_status", table_name="documents")
    op.drop_column("documents", "reviewed_by_id")
    op.drop_column("documents", "reviewed_at")
    op.drop_column("documents", "submitted_at")
    op.drop_column("documents", "review_comment")
    op.drop_column("documents", "review_status")
    op.execute("DROP TYPE document_review_event_kind")
    op.execute("DROP TYPE document_review_status")
