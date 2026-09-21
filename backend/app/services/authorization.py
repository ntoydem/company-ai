"""The single authorization gate (ADR-004).

Every code path that touches documents — listing, download, retrieval, /api/ask —
starts from `allowed_document_ids()`. Nothing bypasses it.

Step 0: single admin user → every existing document is allowed.
Step 1.2: role + department membership + confidentiality rules (SPEC_02 §5).
The signature below is the contract and does not change.
"""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from app.models.user import User
from app.schemas.authorization import AuthorizationScope


class DocumentIdsProvider(Protocol):
    """Supplies the candidate document ids the rules are applied to.

    Phase 0.2 binds this to the documents repository; tests use in-memory fakes.
    """

    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]: ...


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
    # Step 0 stub: one admin user, all documents allowed.
    return set(document_ids_provider.list_document_ids(scope))
