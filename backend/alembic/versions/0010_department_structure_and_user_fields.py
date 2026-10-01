"""Department tree aligned with the product owner's mind map (B-20/1-5), users.title (B-05),
users.primary_department_id (B-09) — Aşama C (docs/plans/ASAMA_C_PLAN.md).

Every data step is guarded with EXISTS: on a fresh database this migration runs before the
seeds (tables empty) and must be a no-op; on an existing database it corrects names, adds
the four new departments, drops the demo `finans` user's second membership (P-5), and
backfills the new columns. Slugs never change — documents, ledger, eval and project
links all key on them.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RENAMES: dict[str, tuple[str, str]] = {  # slug -> (old name, new name)
    "finans": ("Finans", "Proje Finans"),
    "enerji_grubu": ("Enerji Grubu", "Enerji"),
    "enerji_gelistirme": ("Geliştirme", "Proje Geliştirme"),
    "enerji_bakim": ("Bakım", "O&M (İşletme ve Bakım)"),
    "enerji_epc_insaat": ("EPC-İnşaat", "EPC (İnşaat)"),
}
NEW_DEPARTMENTS: tuple[tuple[str, str, str | None], ...] = (  # (slug, name, parent slug)
    ("ik", "İK", None),
    ("enerji_uretim_piyasa", "Üretim/Piyasa", "enerji_grubu"),
    ("mali_isler_muhasebe", "Muhasebe", "mali_isler"),
    ("mali_isler_finansal_muhasebe", "Finansal Muhasebe", "mali_isler"),
)
DEMO_TITLES: dict[str, str] = {
    "admin": "Sistem Yöneticisi",
    "yonetim": "Genel Müdür Yardımcısı",
    "finans": "Proje Finans Uzmanı",
    "hukuk": "Hukuk Müşaviri",
    "enerji": "Enerji Grubu Uzmanı",
}


def upgrade() -> None:
    conn = op.get_bind()

    # --- B-20: names (no-op when the table is empty or already renamed) ---
    for slug, (_old, new) in RENAMES.items():
        conn.execute(
            sa.text(
                "UPDATE departments SET name = CAST(:new AS varchar) "
                "WHERE slug = :slug AND name <> CAST(:new AS varchar)"
            ),
            {"new": new, "slug": slug},
        )
    # --- B-20: four new departments; a child is only added when its parent exists ---
    for slug, name, parent_slug in NEW_DEPARTMENTS:
        if parent_slug is None:
            conn.execute(
                sa.text(
                    "INSERT INTO departments (id, name, slug, parent_id) "
                    "SELECT gen_random_uuid(), CAST(:name AS varchar), CAST(:slug AS varchar), NULL "
                    "WHERE NOT EXISTS (SELECT 1 FROM departments WHERE slug = :slug)"
                ),
                {"name": name, "slug": slug},
            )
        else:
            conn.execute(
                sa.text(
                    "INSERT INTO departments (id, name, slug, parent_id) "
                    "SELECT gen_random_uuid(), CAST(:name AS varchar), CAST(:slug AS varchar), p.id "
                    "FROM departments p "
                    "WHERE p.slug = :parent "
                    "AND NOT EXISTS (SELECT 1 FROM departments WHERE slug = :slug)"
                ),
                {"name": name, "slug": slug, "parent": parent_slug},
            )
    # --- B-20/5: the demo `finans` user belongs to Proje Finans only (P-5) ---
    conn.execute(
        sa.text(
            "DELETE FROM user_departments WHERE user_id = "
            "(SELECT id FROM users WHERE username = 'finans') AND department_id = "
            "(SELECT id FROM departments WHERE slug = 'mali_isler')"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE users SET display_name = 'Proje Finans' "
            "WHERE username = 'finans' AND display_name = 'Finans'"
        )
    )

    # --- B-05 / B-09: new columns ---
    op.add_column("users", sa.Column("title", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("primary_department_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_users_primary_department_id_departments",
        "users",
        "departments",
        ["primary_department_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Backfill: the earliest membership, ties broken by slug (deterministic).
    conn.execute(
        sa.text(
            "UPDATE users u SET primary_department_id = ("
            "  SELECT ud.department_id FROM user_departments ud "
            "  JOIN departments d ON d.id = ud.department_id "
            "  WHERE ud.user_id = u.id ORDER BY ud.created_at, d.slug LIMIT 1"
            ") WHERE u.primary_department_id IS NULL"
        )
    )
    for username, title in DEMO_TITLES.items():
        conn.execute(
            sa.text(
                "UPDATE users SET title = :title WHERE username = :username AND title IS NULL"
            ),
            {"title": title, "username": username},
        )


def downgrade() -> None:
    conn = op.get_bind()
    op.drop_constraint("fk_users_primary_department_id_departments", "users", type_="foreignkey")
    op.drop_column("users", "primary_department_id")
    op.drop_column("users", "title")
    for slug, (old, new) in RENAMES.items():
        conn.execute(
            sa.text("UPDATE departments SET name = :old WHERE slug = :slug AND name = :new"),
            {"old": old, "new": new, "slug": slug},
        )
    # New rows go (memberships/project links cascade); the removed `finans`→`mali_isler`
    # membership is not recreated — it was a deliberate correction, not data to restore.
    for slug, _name, _parent in NEW_DEPARTMENTS:
        conn.execute(sa.text("DELETE FROM departments WHERE slug = :slug"), {"slug": slug})
    conn.execute(
        sa.text(
            "UPDATE users SET display_name = 'Finans' "
            "WHERE username = 'finans' AND display_name = 'Proje Finans'"
        )
    )
