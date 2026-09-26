"""The single authorization gate (ADR-004).

Every code path that touches documents — listing, download, retrieval, /api/ask —
starts from `allowed_document_ids()`. Nothing bypasses it.

Phase 1.2 rules (SPEC_02 §5): `employee` = `normal` documents of the departments they
belong to; `management` = every department, every confidentiality level; `admin` =
everything. Document permission derives from department, not project. `scope` (from
`AuthorizationScope`) only ever narrows the result — it never grants access on its own.
The signature below is the contract and does not change.
"""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from app.models.document import Confidentiality, Document
from app.models.user import User, UserRole
from app.schemas.authorization import AuthorizationScope

_ALL_CONFIDENTIALITY_LEVELS = tuple(Confidentiality)
_EMPLOYEE_CONFIDENTIALITY_LEVELS = (Confidentiality.normal,)


class DocumentIdsProvider(Protocol):
    """Supplies the candidate document ids the rules are applied to.

    Phase 0.2 binds this to the documents repository; tests use in-memory fakes.
    """

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]: ...

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]: ...


def allowed_document_ids(
    user: User,
    scope: AuthorizationScope,
    document_ids_provider: DocumentIdsProvider,
) -> set[UUID]:
    """Return the set of document ids `user` may see within `scope`.

    Invariants (hold in every phase):
    - result ⊆ provider output (scope narrows, never widens)
    - inactive user → empty set
    - empty provider → empty set
    """
    if not user.is_active:
        return set()

    scoped_ids = set(document_ids_provider.list_document_ids(scope))
    if not scoped_ids:
        return set()

    if user.role == UserRole.admin:
        return scoped_ids

    if user.role == UserRole.management:
        role_ids = set(
            document_ids_provider.list_document_ids_for_departments(
                department_slugs=None, confidentiality_levels=_ALL_CONFIDENTIALITY_LEVELS
            )
        )
        return scoped_ids & role_ids

    # employee: normal documents of the departments they belong to.
    department_slugs = [department.slug for department in user.departments]
    if not department_slugs:
        return set()
    role_ids = set(
        document_ids_provider.list_document_ids_for_departments(
            department_slugs=department_slugs,
            confidentiality_levels=_EMPLOYEE_CONFIDENTIALITY_LEVELS,
        )
    )
    return scoped_ids & role_ids


class SingleDocumentIdsProvider:
    """Wraps one document so `allowed_document_ids` can be run in reverse: "can this user
    see this document" instead of "which documents can this user see" (Phase 5.2, the "bu
    belgeyi kim görebilir" admin feature). Reuses the same three-tier rule engine rather
    than writing a second one — the single gate stays the only place permission logic
    lives (ADR-004)."""

    def __init__(self, document: Document) -> None:
        self._document = document

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]:
        del scope  # a single document has nothing left to narrow
        return (self._document.id,)

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        if self._document.confidentiality not in confidentiality_levels:
            return ()
        if department_slugs is not None and self._document.department not in department_slugs:
            return ()
        return (self._document.id,)
