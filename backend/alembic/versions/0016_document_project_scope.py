"""documents.project_scope — explicit `project | group` nature of the project link (Şart 1,
İş Emri 2026-10-15A2, ADR-031).

Backfill: every row with `project_id IS NULL` is a company-level (group) document. The CHECK
keeps the pair consistent from here on; the ORM hook (`models.document._sync_project_scope`)
derives the value on every write, so no writer needs to name the column. Not an
authorization input (ADR-004): the search filter reads it *after* `allowed_document_ids`.

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECK = "ck_documents_project_scope_matches_project_id"


def upgrade() -> None:
    scope = sa.Enum("project", "group", name="project_scope")
    scope.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "documents",
        sa.Column("project_scope", scope, nullable=False, server_default="project"),
    )
    op.execute("UPDATE documents SET project_scope = 'group' WHERE project_id IS NULL")
    op.create_check_constraint(
        _CHECK, "documents", "(project_scope = 'group') = (project_id IS NULL)"
    )


def downgrade() -> None:
    op.drop_constraint(_CHECK, "documents", type_="check")
    op.drop_column("documents", "project_scope")
    sa.Enum(name="project_scope").drop(op.get_bind(), checkfirst=True)
