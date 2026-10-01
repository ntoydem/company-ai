"""folders, folder_grants, folder_grant_events, documents.folder_id (B-26, ADR-023, Aşama E).

Data step (guarded; a no-op on an empty database where the seeds run afterwards): one root
folder per top-level department, named after it, and every document moved into its
department's root. Documents without a department keep `folder_id NULL` (they were already
invisible to every employee). The richer demo tree is B-18's job.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FOLDER_ACCESS = postgresql.ENUM("read", "write", name="folder_access", create_type=False)
ROOT_SENTINEL = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.execute("CREATE TYPE folder_access AS ENUM ('read', 'write')")
    op.create_table(
        "folders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("owner_department_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["folders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_department_id"], ["departments.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_folders_parent_id", "folders", ["parent_id"])
    op.create_index("ix_folders_owner_department_id", "folders", ["owner_department_id"])
    # One name per level; NULL parents (roots) share one bucket through the sentinel.
    op.execute(
        "CREATE UNIQUE INDEX uq_folders_parent_name ON folders "
        f"(COALESCE(parent_id, '{ROOT_SENTINEL}'::uuid), name)"
    )

    op.create_table(
        "folder_grants",
        sa.Column("folder_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("access", FOLDER_ACCESS, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["folder_id"], ["folders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("folder_id", "department_id"),
    )
    op.create_index("ix_folder_grants_department_id", "folder_grants", ["department_id"])

    op.create_table(
        "folder_grant_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_name", sa.String(128), nullable=False),
        sa.Column("folder_id", sa.Uuid(), nullable=True),
        sa.Column("folder_name", sa.String(128), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("department_slug", sa.String(64), nullable=False),
        sa.Column("before", sa.String(5), nullable=False),
        sa.Column("after", sa.String(5), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["folder_id"], ["folders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_folder_grant_events_folder_id", "folder_grant_events", ["folder_id"])

    op.add_column("documents", sa.Column("folder_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_documents_folder_id_folders", "documents", "folders", ["folder_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_documents_folder_id", "documents", ["folder_id"])

    conn = op.get_bind()
    # Root folder per top-level department (no-op on an empty table).
    conn.execute(
        sa.text(
            "INSERT INTO folders (id, name, parent_id, owner_department_id) "
            "SELECT gen_random_uuid(), d.name, NULL, d.id FROM departments d "
            "WHERE d.parent_id IS NULL AND NOT EXISTS ("
            "  SELECT 1 FROM folders f WHERE f.parent_id IS NULL AND f.owner_department_id = d.id)"
        )
    )
    # Existing documents → their department's root folder.
    conn.execute(
        sa.text(
            "UPDATE documents doc SET folder_id = f.id FROM folders f "
            "JOIN departments d ON d.id = f.owner_department_id "
            "WHERE f.parent_id IS NULL AND doc.folder_id IS NULL AND doc.department = d.slug"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_documents_folder_id", table_name="documents")
    op.drop_constraint("fk_documents_folder_id_folders", "documents", type_="foreignkey")
    op.drop_column("documents", "folder_id")
    op.drop_table("folder_grant_events")
    op.drop_table("folder_grants")
    op.execute("DROP INDEX IF EXISTS uq_folders_parent_name")
    op.drop_table("folders")
    op.execute("DROP TYPE folder_access")
