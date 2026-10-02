"""documents.extra_fields, tag_catalog, document_type_guide, admin_events (B-28b, ADR-025).

Data step (guarded; the demo seed builds the same rows on a fresh install): the nine change tags
from BACKEND_GAPS §4.7.4 plus every tag already used on existing documents (as `identity`, so no
existing row becomes invalid under the strict catalogue rule), and the starter guide families from
`app.services.type_family.DEFAULT_GUIDE` — configuration, not truth-ledger data.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-02
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.services.type_family import DEFAULT_CHANGE_TAGS, DEFAULT_GUIDE

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TAG_KIND = postgresql.ENUM("identity", "change", name="tag_kind", create_type=False)


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("extra_fields", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.execute("CREATE TYPE tag_kind AS ENUM ('identity', 'change')")
    op.create_table(
        "tag_catalog",
        sa.Column("slug", sa.String(64), primary_key=True),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("kind", TAG_KIND, nullable=False, server_default="identity"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "document_type_guide",
        sa.Column("family", sa.String(32), primary_key=True),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column(
            "type_patterns", postgresql.ARRAY(sa.String(64)), nullable=False, server_default="{}"
        ),
        sa.Column("suggested_extra_fields", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "suggested_tags", postgresql.ARRAY(sa.String(64)), nullable=False, server_default="{}"
        ),
        sa.Column(
            "standard_fields_emphasis",
            postgresql.ARRAY(sa.String(64)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("prompt_hint", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "admin_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "actor_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("actor_name", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("target", sa.String(128), nullable=False),
        sa.Column("before", sa.Text(), nullable=True),
        sa.Column("after", sa.Text(), nullable=True),
    )
    op.create_index("ix_admin_events_kind", "admin_events", ["kind"])
    # B-28b ledger kind for staff-added extra fields (§4.7.3 "personel ekledi"). Enum values
    # cannot be dropped; 0013's downgrade drops the whole type, so no downgrade step here.
    op.execute("ALTER TYPE document_review_event_kind ADD VALUE IF NOT EXISTS 'field_added'")

    # --- data step: catalogue (change tags + tags already in use) and the starter guide
    conn = op.get_bind()
    for slug, label in DEFAULT_CHANGE_TAGS:
        conn.execute(
            sa.text(
                "INSERT INTO tag_catalog (slug, label, kind) VALUES (:slug, :label, 'change') "
                "ON CONFLICT (slug) DO NOTHING"
            ),
            {"slug": slug, "label": label},
        )
    conn.execute(
        sa.text(
            "INSERT INTO tag_catalog (slug, label, kind) "
            "SELECT DISTINCT t, t, 'identity'::tag_kind FROM documents, unnest(tags) AS t "
            "ON CONFLICT (slug) DO NOTHING"
        )
    )
    for guide in DEFAULT_GUIDE:
        conn.execute(
            sa.text(
                "INSERT INTO document_type_guide (family, label, type_patterns, "
                "suggested_extra_fields, suggested_tags, standard_fields_emphasis, prompt_hint) "
                "VALUES (:family, :label, CAST(:patterns AS varchar[]), CAST(:fields AS jsonb), "
                "CAST(:tags AS varchar[]), CAST(:emphasis AS varchar[]), :hint) "
                "ON CONFLICT (family) DO NOTHING"
            ),
            {
                "family": guide["family"],
                "label": guide["label"],
                "patterns": guide["type_patterns"],
                "fields": json.dumps(guide["suggested_extra_fields"], ensure_ascii=False),
                "tags": guide["suggested_tags"],
                "emphasis": guide["standard_fields_emphasis"],
                "hint": guide["prompt_hint"],
            },
        )


def downgrade() -> None:
    op.drop_index("ix_admin_events_kind", table_name="admin_events")
    op.drop_table("admin_events")
    op.drop_table("document_type_guide")
    op.drop_table("tag_catalog")
    op.execute("DROP TYPE tag_kind")
    op.drop_column("documents", "extra_fields")
