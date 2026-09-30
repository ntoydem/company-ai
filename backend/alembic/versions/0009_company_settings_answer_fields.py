"""company_settings (B-25 product layer key, one row) + audit_log.product_level / warnings
(Aşama A "Balbal cevap döngüsü", docs/plans/ASAMA_A_BALBAL_DONGUSU_PLAN.md)

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "company_settings",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column(
            "enabled_products",
            postgresql.ARRAY(sa.String(2)),
            nullable=False,
            server_default="{P1,P2,P3}",
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("id = 1", name="company_settings_single_row"),
        sa.CheckConstraint(
            "enabled_products <@ ARRAY['P1','P2','P3']::varchar[]",
            name="company_settings_known_products",
        ),
    )
    # The one row: demo default = every layer open. Never created by application code.
    op.execute("INSERT INTO company_settings (id) VALUES (1)")

    # Written per /api/ask row from now on; older rows stay NULL / [] — no backfill guess.
    op.add_column("audit_log", sa.Column("product_level", sa.String(2), nullable=True))
    op.add_column(
        "audit_log",
        sa.Column(
            "warnings", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )


def downgrade() -> None:
    op.drop_column("audit_log", "warnings")
    op.drop_column("audit_log", "product_level")
    op.drop_table("company_settings")
