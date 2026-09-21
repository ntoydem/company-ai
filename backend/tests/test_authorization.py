"""Contract tests for the single authorization gate (ADR-004)."""

import uuid
from collections.abc import Iterable
from uuid import UUID

from app.models.user import User, UserRole
from app.schemas.authorization import AuthorizationScope
from app.services.authorization import allowed_document_ids


class FakeProvider:
    def __init__(self, ids: Iterable[UUID]) -> None:
        self.ids = list(ids)
        self.seen_scopes: list[AuthorizationScope] = []

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]:
        self.seen_scopes.append(scope)
        return iter(self.ids)


def _user(role: UserRole = UserRole.admin, active: bool = True) -> User:
    return User(
        username=f"u-{role.value}",
        password_hash="x",
        display_name="Test",
        role=role,
        is_active=active,
    )


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
