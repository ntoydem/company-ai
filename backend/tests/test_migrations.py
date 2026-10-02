"""`alembic upgrade head` on an empty database, and back."""

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.db import get_engine
from tests.conftest import alembic_config


def _current_revision() -> str | None:
    with get_engine().connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def test_downgrade_to_empty_then_upgrade_head() -> None:
    cfg = alembic_config()
    engine = get_engine()

    command.downgrade(cfg, "base")
    assert _current_revision() is None
    assert "users" not in inspect(engine).get_table_names()

    command.upgrade(cfg, "head")
    assert _current_revision() == "0013"
    tables = inspect(engine).get_table_names()
    assert "users" in tables
    assert "documents" in tables
    assert "document_pages" in tables
    assert "document_chunks" in tables
    assert "ingestion_jobs" in tables
    assert "departments" in tables
    assert "user_departments" in tables
    assert "projects" in tables
    assert "project_departments" in tables
    assert "document_metadata_suggestions" in tables
    assert "audit_log" in tables
    document_columns = {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "external_ref" in document_columns
    assert "ai_suggestion_id" in document_columns
    suggestion_columns = {
        c["name"] for c in inspect(engine).get_columns("document_metadata_suggestions")
    }
    assert {"document_id", "model", "status", "fields", "error"} <= suggestion_columns
    audit_columns = {c["name"] for c in inspect(engine).get_columns("audit_log")}
    assert "chunks_retrieved" in audit_columns
    document_columns = {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "has_macros" in document_columns
    assert "file_name" in document_columns
    assert {
        "user_id",
        "timestamp",
        "question",
        "query_type",
        "documents_retrieved",
        "sources",
        "cost_estimate",
        "execution_ms",
        "request_id",
        "error",
    } <= audit_columns

    assert {"product_level", "warnings"} <= audit_columns
    user_columns = {c["name"] for c in inspect(engine).get_columns("users")}
    assert {"title", "primary_department_id"} <= user_columns
    assert {"folders", "folder_grants", "folder_grant_events"} <= set(tables)
    assert "folder_id" in {c["name"] for c in inspect(engine).get_columns("documents")}
    assert "company_settings" in tables
    assert "document_review_events" in tables
    assert "review_status" in {c["name"] for c in inspect(engine).get_columns("documents")}

    with engine.connect() as conn:
        has_vector = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        # Migration 0009 inserts the one settings row (demo default: every layer open)
        # and the table refuses a second one.
        rows = conn.execute(text("SELECT id, enabled_products FROM company_settings")).all()
        with pytest.raises(IntegrityError):
            conn.execute(text("INSERT INTO company_settings (id) VALUES (2)"))
    assert has_vector == 1
    assert rows == [(1, ["P1", "P2", "P3"])]


def test_upgrade_head_is_idempotent() -> None:
    command.upgrade(alembic_config(), "head")
    assert _current_revision() == "0013"


def test_0010_corrects_an_existing_phase_1_2_tree_and_backfills_users() -> None:
    """Aşama C, C-02: the migration path and the seed path must end in the same tree. Here
    the pre-Aşama-C tree (old names, no İK/Üretim/Piyasa/Mali İşler children) and the demo
    `finans` user with both memberships are planted at revision 0009, then upgraded."""
    from app.repositories.department_repo import list_all
    from app.services.demo_departments_seed import _DEPARTMENTS
    from tests.test_department_structure import tree_snapshot

    cfg = alembic_config()
    engine = get_engine()
    command.downgrade(cfg, "0009")
    old_tree = [
        ("enerji_grubu", "Enerji Grubu", None),
        ("enerji_gelistirme", "Geliştirme", "enerji_grubu"),
        ("enerji_epc_insaat", "EPC-İnşaat", "enerji_grubu"),
        ("enerji_bakim", "Bakım", "enerji_grubu"),
        ("finans", "Finans", None),
        ("hukuk", "Hukuk", None),
        ("mali_isler", "Mali İşler", None),
        ("idari_isler", "İdari İşler", None),
    ]
    with engine.begin() as conn:
        for slug, name, parent in old_tree:
            conn.execute(
                text(
                    "INSERT INTO departments (id, name, slug, parent_id) VALUES "
                    "(gen_random_uuid(), :name, :slug, "
                    "(SELECT id FROM departments WHERE slug = :parent))"
                ),
                {"name": name, "slug": slug, "parent": parent},
            )
        conn.execute(
            text(
                "INSERT INTO users (id, username, password_hash, display_name, role) VALUES "
                "(gen_random_uuid(), 'finans', 'x', 'Finans', 'employee'), "
                "(gen_random_uuid(), 'hukuk', 'x', 'Hukuk', 'employee'), "
                "(gen_random_uuid(), 'yonetim', 'x', 'Yönetim', 'management')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO user_departments (user_id, department_id) "
                "SELECT u.id, d.id FROM users u, departments d "
                "WHERE (u.username = 'finans' AND d.slug IN ('finans', 'mali_isler')) "
                "   OR (u.username = 'hukuk' AND d.slug = 'hukuk')"
            )
        )

    command.upgrade(cfg, "head")

    from app.core.db import get_session_factory

    with get_session_factory()() as session:
        assert tree_snapshot(list_all(session)) == tree_snapshot_from_seed(_DEPARTMENTS)
        rows = session.execute(
            text(
                "SELECT u.username, u.display_name, u.title, pd.slug AS primary_slug, "
                "array_agg(d.slug ORDER BY d.slug) AS memberships "
                "FROM users u LEFT JOIN departments pd ON pd.id = u.primary_department_id "
                "LEFT JOIN user_departments ud ON ud.user_id = u.id "
                "LEFT JOIN departments d ON d.id = ud.department_id "
                "GROUP BY u.username, u.display_name, u.title, pd.slug ORDER BY u.username"
            )
        ).all()
    by_user = {r.username: r for r in rows}
    assert by_user["finans"].memberships == ["finans"]  # mali_isler membership dropped (P-5)
    assert by_user["finans"].primary_slug == "finans"
    assert by_user["finans"].display_name == "Proje Finans"
    assert by_user["finans"].title == "Proje Finans Uzmanı"
    assert by_user["hukuk"].primary_slug == "hukuk" and by_user["hukuk"].title == "Hukuk Müşaviri"
    assert by_user["yonetim"].primary_slug is None and by_user["yonetim"].memberships == [None]


def tree_snapshot_from_seed(
    seed: tuple[tuple[str, str, str | None], ...],
) -> list[tuple[str, str, str | None]]:
    return sorted(seed, key=lambda row: row[1])


def test_0011_creates_root_folders_and_moves_existing_documents() -> None:
    """Aşama E, E-12: on an existing database every top-level department gets a root folder
    and every document lands in its department's root; department-less documents stay
    folder-less; sub-departments get no root of their own."""
    cfg = alembic_config()
    engine = get_engine()
    command.downgrade(cfg, "0010")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO departments (id, name, slug, parent_id) VALUES "
                "(gen_random_uuid(), 'Hukuk', 'hukuk', NULL), "
                "(gen_random_uuid(), 'Enerji', 'enerji_grubu', NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO departments (id, name, slug, parent_id) VALUES "
                "(gen_random_uuid(), 'Proje Geliştirme', 'enerji_gelistirme', "
                "(SELECT id FROM departments WHERE slug = 'enerji_grubu'))"
            )
        )
        for title, department in (("A", "hukuk"), ("B", "enerji_grubu"), ("C", None)):
            conn.execute(
                text(
                    "INSERT INTO documents (id, title, document_type, counterparty, document_date, "
                    "status, department, storage_path, ingestion_status, source, confidentiality, "
                    "tags, related_document_ids, version) VALUES (gen_random_uuid(), :title, 't', "
                    "'c', '2026-01-01', 'executed', :department, 'x/original.pdf', 'ready', 'web', "
                    "'normal', '{}', '{}', 1)"
                ),
                {"title": title, "department": department},
            )

    command.upgrade(cfg, "head")

    with engine.connect() as conn:
        roots = conn.execute(
            text(
                "SELECT f.name, d.slug FROM folders f "
                "JOIN departments d ON d.id = f.owner_department_id "
                "WHERE f.parent_id IS NULL ORDER BY d.slug"
            )
        ).all()
        placed = conn.execute(
            text(
                "SELECT doc.title, f.name FROM documents doc "
                "LEFT JOIN folders f ON f.id = doc.folder_id ORDER BY doc.title"
            )
        ).all()
    assert [tuple(r) for r in roots] == [
        ("Enerji", "enerji_grubu"),
        ("Hukuk", "hukuk"),
    ]  # no root for the sub-department
    assert [tuple(r) for r in placed] == [("A", "Hukuk"), ("B", "Enerji"), ("C", None)]


_ENUM_LABELS = "SELECT unnest(enum_range(NULL::user_role))::text"


def test_0012_adds_department_manager_and_downgrade_demotes_to_employee() -> None:
    """B-08 (M-10): the enum gains the value on upgrade; on downgrade PostgreSQL cannot drop
    an enum label, so the type is rebuilt and managers fall back to `employee`."""
    cfg = alembic_config()
    engine = get_engine()
    command.upgrade(cfg, "head")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users"))
        conn.execute(
            text(
                "INSERT INTO users (id, username, password_hash, display_name, role) VALUES "
                "(gen_random_uuid(), 'm1', 'x', 'M', 'department_manager'), "
                "(gen_random_uuid(), 'e1', 'x', 'E', 'employee')"
            )
        )
        labels = conn.execute(text(_ENUM_LABELS)).scalars().all()
    assert "department_manager" in labels

    command.downgrade(cfg, "0011")

    with engine.connect() as conn:
        labels = conn.execute(text(_ENUM_LABELS)).scalars().all()
        roles = conn.execute(text("SELECT username, role::text FROM users ORDER BY username")).all()
    assert labels == ["admin", "management", "employee"]
    assert [tuple(r) for r in roles] == [("e1", "employee"), ("m1", "employee")]
    command.upgrade(cfg, "head")
