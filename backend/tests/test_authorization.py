"""Contract tests for the single authorization gate (ADR-004)."""

import uuid
from collections.abc import Iterable
from uuid import UUID

from app.models.department import Department
from app.models.document import Confidentiality
from app.models.user import User, UserRole
from app.schemas.authorization import AuthorizationScope
from app.services.authorization import allowed_document_ids


class FakeProvider:
    def __init__(self, ids: Iterable[UUID], department_ids: Iterable[UUID] | None = None) -> None:
        self.ids = list(ids)
        self.department_ids = list(department_ids) if department_ids is not None else list(self.ids)
        self.seen_scopes: list[AuthorizationScope] = []
        self.seen_department_calls: list[
            tuple[tuple[str, ...] | None, tuple[Confidentiality, ...]]
        ] = []
        # B-26: documents reachable through folder grants (empty unless a test sets it).
        self.folder_grant_ids: list[UUID] = []
        self.seen_folder_calls: list[tuple[tuple[str, ...], tuple[Confidentiality, ...]]] = []
        # B-28: pending documents the caller may handle (empty unless a test sets it).
        self.pending_ids: list[UUID] = []
        self.seen_pending_calls: list[tuple[UUID, tuple[str, ...] | None]] = []

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]:
        self.seen_scopes.append(scope)
        return iter(self.ids)

    def list_document_ids_for_folder_grants(
        self,
        *,
        department_slugs: Iterable[str],
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        self.seen_folder_calls.append((tuple(department_slugs), tuple(confidentiality_levels)))
        return iter(self.folder_grant_ids)

    def list_pending_document_ids(
        self,
        *,
        uploaded_by_id: UUID,
        manager_department_slugs: Iterable[str] | None,
    ) -> Iterable[UUID]:
        slugs = None if manager_department_slugs is None else tuple(manager_department_slugs)
        self.seen_pending_calls.append((uploaded_by_id, slugs))
        return iter(self.pending_ids)

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        self.seen_department_calls.append(
            (
                tuple(department_slugs) if department_slugs is not None else None,
                tuple(confidentiality_levels),
            )
        )
        return iter(self.department_ids)


def _user(
    role: UserRole = UserRole.admin,
    active: bool = True,
    department_slugs: Iterable[str] = (),
) -> User:
    user = User(
        username=f"u-{role.value}",
        password_hash="x",
        display_name="Test",
        role=role,
        is_active=active,
    )
    for slug in department_slugs:
        user.departments.append(Department(name=slug, slug=slug))
    return user


def test_step0_stub_returns_all_provided_ids() -> None:
    ids = {uuid.uuid4() for _ in range(3)}
    provider = FakeProvider(ids)
    result = allowed_document_ids(_user(), AuthorizationScope(), provider)
    assert result == ids
    assert isinstance(result, set)


def test_empty_provider_yields_empty_set() -> None:
    assert allowed_document_ids(_user(), AuthorizationScope(), FakeProvider([])) == set()


def test_inactive_user_yields_empty_set() -> None:
    provider = FakeProvider([uuid.uuid4()])
    assert allowed_document_ids(_user(active=False), AuthorizationScope(), provider) == set()


def test_result_is_subset_of_provider_and_scope_is_forwarded() -> None:
    ids = [uuid.uuid4(), uuid.uuid4()]
    provider = FakeProvider(ids)
    scope = AuthorizationScope(department="finance", project_id=uuid.uuid4())
    result = allowed_document_ids(_user(UserRole.employee), scope, provider)
    assert result <= set(ids)
    assert provider.seen_scopes == [scope]


# --- Phase 1.2: role + department membership + confidentiality rules (SPEC_02 §5) ---


def test_admin_sees_everything_without_a_department_check() -> None:
    ids = {uuid.uuid4() for _ in range(2)}
    provider = FakeProvider(ids)
    result = allowed_document_ids(_user(UserRole.admin), AuthorizationScope(), provider)
    assert result == ids
    assert provider.seen_department_calls == []


def test_management_sees_all_departments_and_confidentiality_levels() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    provider = FakeProvider({a, b}, department_ids={a})
    result = allowed_document_ids(_user(UserRole.management), AuthorizationScope(), provider)
    assert result == {a}
    (department_slugs, confidentiality_levels) = provider.seen_department_calls[0]
    assert department_slugs is None
    assert set(confidentiality_levels) == set(Confidentiality)


def test_employee_without_department_membership_sees_nothing() -> None:
    provider = FakeProvider({uuid.uuid4()})
    result = allowed_document_ids(_user(UserRole.employee), AuthorizationScope(), provider)
    assert result == set()
    assert provider.seen_department_calls == []  # no departments — never even asked


def test_employee_sees_only_own_department_normal_documents() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    provider = FakeProvider({a, b, c}, department_ids={a, b})
    result = allowed_document_ids(
        _user(UserRole.employee, department_slugs=["finans"]), AuthorizationScope(), provider
    )
    assert result == {a, b}
    (department_slugs, confidentiality_levels) = provider.seen_department_calls[0]
    assert department_slugs == ("finans",)
    assert confidentiality_levels == (Confidentiality.normal,)


def test_role_based_result_is_still_intersected_with_scope() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    provider = FakeProvider({a, b}, department_ids={a})  # role only allows `a`
    scope = AuthorizationScope(department="finans")
    result = allowed_document_ids(
        _user(UserRole.employee, department_slugs=["finans"]), scope, provider
    )
    assert result == {a}
    assert provider.seen_scopes == [scope]


# --- B-08 (02.10.2026): department_manager = own departments at normal + restricted ---


def test_department_manager_sees_own_department_normal_and_restricted_but_not_board() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    provider = FakeProvider({a, b}, department_ids={a})
    result = allowed_document_ids(
        _user(UserRole.department_manager, department_slugs=["finans"]),
        AuthorizationScope(),
        provider,
    )
    assert result == {a}
    (department_slugs, confidentiality_levels) = provider.seen_department_calls[0]
    assert department_slugs == ("finans",)  # only the departments they belong to (M-02)
    assert confidentiality_levels == (Confidentiality.normal, Confidentiality.restricted)
    assert Confidentiality.board not in confidentiality_levels  # M-01


def test_department_manager_folder_grants_use_the_same_two_levels() -> None:
    own, granted, other = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    provider = FakeProvider({own, granted, other}, department_ids={own})
    provider.folder_grant_ids = [granted]
    result = allowed_document_ids(
        _user(UserRole.department_manager, department_slugs=["finans"]),
        AuthorizationScope(),
        provider,
    )
    assert result == {own, granted}
    assert provider.seen_folder_calls == [
        (("finans",), (Confidentiality.normal, Confidentiality.restricted))
    ]  # M-03


def test_department_manager_without_membership_or_inactive_sees_nothing() -> None:
    provider = FakeProvider({uuid.uuid4()})
    assert (
        allowed_document_ids(_user(UserRole.department_manager), AuthorizationScope(), provider)
        == set()
    )
    assert provider.seen_department_calls == []
    inactive = _user(UserRole.department_manager, active=False, department_slugs=["finans"])
    assert allowed_document_ids(inactive, AuthorizationScope(), provider) == set()  # M-04


def test_employee_levels_are_unchanged_by_the_manager_rule() -> None:
    provider = FakeProvider({uuid.uuid4()})
    allowed_document_ids(
        _user(UserRole.employee, department_slugs=["finans"]), AuthorizationScope(), provider
    )
    assert provider.seen_department_calls[0][1] == (Confidentiality.normal,)
    assert provider.seen_folder_calls[0][1] == (Confidentiality.normal,)


# --- Adım 1 / Soru 15 (Tansu A, 09.10.2026): the gate on the real seeded demo set ---


def test_finans_employee_sees_the_financial_model_but_still_no_restricted_document(
    db_session, settings
) -> None:
    """End-to-end through the SQL provider: the Proje Finans *specialist* (`finans`, role
    employee) now gets `DOC-ANK-FIN-008` (Financial Model 2026, `normal` since Soru 15),
    while a `restricted` document of the same department stays outside the gate and `board`
    stays outside too (rules unchanged, only the data changed)."""
    from pathlib import Path

    from app.models.document import Document
    from app.repositories import user_repo
    from app.repositories.document_repo import SqlDocumentIdsProvider, get_by_external_ref
    from app.services.admin_seed import ensure_admin_user
    from app.services.demo_departments_seed import (
        ensure_demo_department_memberships,
        ensure_demo_departments,
    )
    from app.services.demo_documents_seed import ensure_demo_documents
    from app.services.demo_projects_seed import ensure_demo_projects
    from app.services.demo_users_seed import ensure_demo_users

    manifest = Path(__file__).resolve().parent.parent / "seed_data" / "documents" / "manifest.json"
    ensure_admin_user(db_session, settings)
    ensure_demo_users(db_session, settings)
    ensure_demo_departments(db_session, settings)
    ensure_demo_department_memberships(db_session, settings)
    ensure_demo_projects(db_session, settings)
    ensure_demo_documents(db_session, settings, manifest)
    model = get_by_external_ref(db_session, "DOC-ANK-FIN-008")
    covenant = get_by_external_ref(db_session, "DOC-ANK-FIN-009")
    assert model is not None and covenant is not None
    covenant.confidentiality = Confidentiality.restricted  # a restricted finans document
    board = Document(
        title="Board only",
        document_type="minutes",
        counterparty="x",
        document_date=model.document_date,
        department="finans",
        confidentiality=Confidentiality.board,
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    db_session.add(board)
    db_session.commit()
    finans = user_repo.get_by_username(db_session, "finans")
    assert finans is not None and finans.role == UserRole.employee

    allowed = allowed_document_ids(finans, AuthorizationScope(), SqlDocumentIdsProvider(db_session))

    assert model.id in allowed
    assert covenant.id not in allowed
    assert board.id not in allowed
