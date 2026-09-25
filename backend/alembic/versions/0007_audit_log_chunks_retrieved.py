"""audit_log.chunks_retrieved (Phase 3.2b, SPEC_06 §1 at page level)

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Which (document, page) pairs actually reached the prompt — `documents_retrieved`
    # only says which documents. Needed to tell a retrieval miss from a model refusal
    # after the fact (docs/plans/PHASE_3_2B_PLAN.md T3).
    op.add_column(
        "audit_log",
        sa.Column("chunks_retrieved", postgresql.JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("audit_log", "chunks_retrieved")
