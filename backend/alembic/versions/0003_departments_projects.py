"""departments, user_departments, projects, project_departments

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROJECT_STAGE = postgresql.ENUM(
    "development", "construction", "operation", name="project_stage", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE TYPE project_stage AS ENUM ('development', 'construction', 'operation')")

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_departments_slug", "departments", ["slug"], unique=True)
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"])

    op.create_table(
        "user_departments",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "department_id"),
    )
    op.create_index("ix_user_departments_department_id", "user_departments", ["department_id"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("stage", PROJECT_STAGE, nullable=False, server_default="development"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_projects_code", "projects", ["code"], unique=True)

    op.create_table(
        "project_departments",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "department_id"),
    )
    op.create_index(
        "ix_project_departments_department_id", "project_departments", ["department_id"]
    )

    op.create_foreign_key(
        "fk_documents_project_id_projects",
        "documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_project_id_projects", "documents", type_="foreignkey")

    op.drop_index("ix_project_departments_department_id", table_name="project_departments")
    op.drop_table("project_departments")

    op.drop_index("ix_projects_code", table_name="projects")
    op.drop_table("projects")
    op.execute("DROP TYPE project_stage")

    op.drop_index("ix_user_departments_department_id", table_name="user_departments")
    op.drop_table("user_departments")

    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_index("ix_departments_slug", table_name="departments")
    op.drop_table("departments")
