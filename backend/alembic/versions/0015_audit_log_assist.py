"""audit_log.assist — the code-generated assist block the user saw (ADR-027, Tansu Not 2).

NULL while ASSIST_MODE is off (today's default) and for every row written before this
migration; stored, not derived, so what the user was shown stays auditable (rule 4).

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("assist", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_log", "assist")
