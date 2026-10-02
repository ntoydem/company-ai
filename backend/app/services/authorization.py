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

B-28 (02.10.2026, ADR-024): a document also has a publication state. Every rule above sees
**approved** documents only — retrieval, search, `/api/ask` and the Excel catalogue never
touch a pending one. With `scope.include_pending=True` (document-handling endpoints) the
result additionally contains the pending documents the caller may *handle*: their own
uploads, the pending documents of the departments a `department_manager` manages, and —
for `admin` — every pending document. `management` sees no pending document (NOT §5.2:
no general privilege, not an approver). Still one function, one more input.
"""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from app.models.document import Confidentiality, Document, DocumentReviewStatus
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

    def list_pending_document_ids(
        self,
        *,
        uploaded_by_id: UUID,
        manager_department_slugs: Iterable[str] | None,
    ) -> Iterable[UUID]:
        """B-28: not-yet-approved documents uploaded by `uploaded_by_id` or belonging to one
        of `manager_department_slugs`; `None` = every pending document (admin)."""
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
        # Published documents are all theirs; pending ones only when the caller asked to
        # handle them (B-28) — `scoped_ids` already excludes pending rows otherwise.
        return scoped_ids

    if user.role == UserRole.management:
        management_ids = set(
            document_ids_provider.list_document_ids_for_departments(
                department_slugs=None, confidentiality_levels=_ALL_CONFIDENTIALITY_LEVELS
            )
        )
        return scoped_ids & management_ids

    # employee / department_manager: documents of the departments they belong to, plus
    # (B-26) documents in folders those departments were granted access to — both at the
    # role's confidentiality levels (`normal`; managers also `restricted`, B-08).
    department_slugs = [department.slug for department in user.departments]
    role_ids: set[UUID] = set()
    if department_slugs:
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
    if scope.include_pending:
        # B-28: own uploads always; the departments' pending documents only for a manager.
        manager_slugs = department_slugs if user.role == UserRole.department_manager else ()
        role_ids |= set(
            document_ids_provider.list_pending_document_ids(
                uploaded_by_id=user.id, manager_department_slugs=manager_slugs
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

    @property
    def _approved(self) -> bool:
        return self._document.review_status == DocumentReviewStatus.approved

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]:
        # Nothing left to narrow by department/project; the publication filter still applies.
        if not self._approved and not scope.include_pending:
            return ()
        return (self._document.id,)

    def list_pending_document_ids(
        self,
        *,
        uploaded_by_id: UUID,
        manager_department_slugs: Iterable[str] | None,
    ) -> Iterable[UUID]:
        if self._approved:
            return ()
        if manager_department_slugs is None or self._document.uploaded_by_id == uploaded_by_id:
            return (self._document.id,)
        if self._document.department is not None and self._document.department in list(
            manager_department_slugs
        ):
            return (self._document.id,)
        return ()

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]:
        if not self._approved or self._document.confidentiality not in confidentiality_levels:
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
        if not self._approved or self._document.confidentiality not in confidentiality_levels:
            return ()
        if self._folder_grantee_slugs.isdisjoint(department_slugs):
            return ()
        return (self._document.id,)
