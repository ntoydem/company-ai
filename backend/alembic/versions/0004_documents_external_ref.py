"""documents.external_ref (Phase 3.1 seed idempotency key)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("external_ref", sa.String(64), nullable=True))
    op.create_index(
        "ix_documents_external_ref", "documents", ["external_ref"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_documents_external_ref", table_name="documents")
    op.drop_column("documents", "external_ref")
