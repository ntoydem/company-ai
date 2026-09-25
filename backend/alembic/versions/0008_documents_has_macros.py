"""documents.has_macros + file_name (Phase 4.2: macros flagged never executed; workbook citations
need the original file name, `storage_path` only says original.xlsx)

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("has_macros", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("documents", sa.Column("file_name", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "file_name")
    op.drop_column("documents", "has_macros")
