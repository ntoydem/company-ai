"""The single authorization gate (ADR-004).

Every code path that touches documents — listing, download, retrieval, /api/ask —
starts from `allowed_document_ids()`. Nothing bypasses it.

Phase 1.2 rules (SPEC_02 §5): `employee` = `normal` documents of the departments they
belong to; `management` = every department, every confidentiality level; `admin` =
everything. Document permission derives from department, not project. `scope` (from
`AuthorizationScope`) only ever narrows the result — it never grants access on its own.
The signature below is the contract and does not change.

Aşama E (B-26, ADR-023): an `employee` additionally sees the documents of folders their
departments were granted access to (`read` or `write`, inherited down the tree) — at the
same confidentiality levels as their own departments, never more. Folder grants are one
more *input* to this function, not a second gate; `management`/`admin` are unchanged.

B-08 (02.10.2026): `department_manager` = the `employee` rule with one more confidentiality
level — the `normal` **and** `restricted` documents of the departments they belong to
(memberships, plus folder grants at the same two levels), never `board` and never another
department. The rule is fixed code, not a per-customer table (NOT §5.1); the customer admin
only decides *who* holds the role. `management`/`admin` are unchanged.
"""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from app.models.document import Confidentiality, Document
from app.models.user import User, UserRole
from app.schemas.authorization import AuthorizationScope

_ALL_CONFIDENTIALITY_LEVELS = tuple(Confidentiality)
_EMPLOYEE_CONFIDENTIALITY_LEVELS = (Confidentiality.normal,)
_MANAGER_CONFIDENTIALITY_LEVELS = (Confidentiality.normal, Confidentiality.restricted)


def _membership_confidentiality_levels(role: UserRole) -> tuple[Confidentiality, ...]:
    """Levels a membership-based role sees in its own departments (B-08): `board` is never
    among them — that stays `management`/`admin` only (NOT §7.2 #1, Naci 02.10.2026)."""
    if role == UserRole.department_manager:
        return _MANAGER_CONFIDENTIALITY_LEVELS
    return _EMPLOYEE_CONFIDENTIALITY_LEVELS


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

    def list_document_ids_for_folder_grants(
        self,
        *,
        department_slugs: Iterable[str],
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        """Documents in folders (and sub-folders) that any of `department_slugs` was granted
        access to (B-26), limited to `confidentiality_levels`."""
        ...


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

    # employee / department_manager: documents of the departments they belong to, plus
    # (B-26) documents in folders those departments were granted access to — both at the
    # role's confidentiality levels (`normal`; managers also `restricted`, B-08).
    department_slugs = [department.slug for department in user.departments]
    if not department_slugs:
        return set()
    levels = _membership_confidentiality_levels(user.role)
    role_ids = set(
        document_ids_provider.list_document_ids_for_departments(
            department_slugs=department_slugs, confidentiality_levels=levels
        )
    )
    role_ids |= set(
        document_ids_provider.list_document_ids_for_folder_grants(
            department_slugs=department_slugs, confidentiality_levels=levels
        )
    )
    return scoped_ids & role_ids


class SingleDocumentIdsProvider:
    """Wraps one document so `allowed_document_ids` can be run in reverse: "can this user
    see this document" instead of "which documents can this user see" (Phase 5.2, the "bu
    belgeyi kim görebilir" admin feature). Reuses the same three-tier rule engine rather
    than writing a second one — the single gate stays the only place permission logic
    lives (ADR-004)."""

    def __init__(
        self, document: Document, folder_grantee_slugs: frozenset[str] = frozenset()
    ) -> None:
        self._document = document
        # Departments with effective (own or inherited) access to the document's folder —
        # computed by the caller from `folder_repo.access_map()`, so this adapter stays free
        # of SQL and the rule stays in one place (B-26).
        self._folder_grantee_slugs = folder_grantee_slugs

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
        if department_slugs is not None and (
            self._document.department is None or self._document.department not in department_slugs
        ):
            return ()
        return (self._document.id,)

    def list_document_ids_for_folder_grants(
        self,
        *,
        department_slugs: Iterable[str],
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        if self._document.confidentiality not in confidentiality_levels:
            return ()
        if self._folder_grantee_slugs.isdisjoint(department_slugs):
            return ()
        return (self._document.id,)
