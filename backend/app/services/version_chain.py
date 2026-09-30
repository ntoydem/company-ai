"""Deterministic version-chain evaluation (ADR-012): old ≠ wrong.

Given the documents visible to the user, compute for each one where it sits in its
`supersedes` chain and whether it is the *current* link on `DEMO_TODAY`. The LLM only
reads these flags; it never derives them itself.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.models.document import Document


@dataclass(frozen=True)
class ChainPosition:
    position: int
    chain_length: int
    in_force: bool
    is_current: bool
    is_initial: bool
    has_predecessor: bool
    has_successor: bool
    supersedes_title: str | None
    superseded_by_title: str | None
    # Ids of the *loaded* neighbours only — a link the user may not see is never loaded
    # (`document_repo.load_with_chains`), so it stays `None` here exactly like its title.
    supersedes_document_id: UUID | None = None
    superseded_by_document_id: UUID | None = None


def is_in_force(document: Document, today: date) -> bool:
    start = document.effective_date or document.document_date
    if start > today:
        return False
    return document.expiration_date is None or document.expiration_date > today


def _chains(by_id: dict[UUID, Document]) -> list[list[Document]]:
    """Split the loaded documents into ordered chains (oldest first). A link whose
    predecessor is not loaded starts a chain; cycles are cut at the first revisit."""
    chains: list[list[Document]] = []
    placed: set[UUID] = set()
    for document in by_id.values():
        if document.id in placed:
            continue
        predecessor = document.supersedes_document_id
        if predecessor is not None and predecessor in by_id:
            continue  # will be reached from its root
        chain: list[Document] = []
        current: Document | None = document
        while current is not None and current.id not in placed:
            chain.append(current)
            placed.add(current.id)
            successor = current.superseded_by_document_id
            current = by_id.get(successor) if successor is not None else None
        chains.append(chain)
    # Documents only reachable through a cycle (no root) become singleton chains.
    for document in by_id.values():
        if document.id not in placed:
            placed.add(document.id)
            chains.append([document])
    return chains


def evaluate_version_chains(
    documents: Iterable[Document], today: date
) -> dict[UUID, ChainPosition]:
    by_id = {document.id: document for document in documents}
    result: dict[UUID, ChainPosition] = {}
    for chain in _chains(by_id):
        # "Current" = the last link in force on `today` that is not superseded by a
        # document we cannot see.
        current_id: UUID | None = None
        for document in chain:
            hidden_successor = (
                document.superseded_by_document_id is not None
                and document.superseded_by_document_id not in by_id
            )
            if is_in_force(document, today) and not hidden_successor:
                current_id = document.id
        for index, document in enumerate(chain):
            predecessor_id = document.supersedes_document_id
            successor_id = document.superseded_by_document_id
            predecessor = by_id.get(predecessor_id) if predecessor_id else None
            successor = by_id.get(successor_id) if successor_id else None
            result[document.id] = ChainPosition(
                position=index + 1,
                chain_length=len(chain),
                in_force=is_in_force(document, today),
                is_current=document.id == current_id,
                is_initial=index == 0 and document.supersedes_document_id is None,
                has_predecessor=document.supersedes_document_id is not None,
                has_successor=document.superseded_by_document_id is not None,
                supersedes_title=predecessor.title if predecessor else None,
                superseded_by_title=successor.title if successor else None,
                supersedes_document_id=predecessor.id if predecessor else None,
                superseded_by_document_id=successor.id if successor else None,
            )
    return result
