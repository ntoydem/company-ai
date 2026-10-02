"""user_role enum gains `department_manager` (B-08, ADR-004 concretization).

No data step: nobody is promoted automatically — the customer admin assigns the role per
person via `PATCH /api/users/{id}` (NOT §8.1). `ADD VALUE IF NOT EXISTS` keeps the upgrade
idempotent; the new label is not used inside this migration, so running it within Alembic's
transaction is fine (PostgreSQL only forbids *using* a value added in the same transaction).

Downgrade: PostgreSQL cannot drop an enum value, so the type is rebuilt — managers fall back
to `employee` first (the closest rule: own departments, `normal` only).

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-02
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'department_manager'")


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'employee' WHERE role = 'department_manager'")
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'management', 'employee')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role"
    )
    op.execute("DROP TYPE user_role_old")
