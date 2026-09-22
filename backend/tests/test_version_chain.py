"""`evaluate_version_chains` (ADR-012) — pure in-memory documents, no database."""

import uuid
from datetime import date

from app.models.document import Document
from app.services.version_chain import evaluate_version_chains, is_in_force

TODAY = date(2026, 9, 15)


def _doc(
    title: str,
    document_date: date,
    *,
    effective_date: date | None = None,
    expiration_date: date | None = None,
) -> Document:
    return Document(
        id=uuid.uuid4(),
        title=title,
        document_type="t",
        counterparty="c",
        document_date=document_date,
        effective_date=effective_date,
        expiration_date=expiration_date,
        storage_path="x",
    )


def _link(older: Document, newer: Document) -> None:
    newer.supersedes_document_id = older.id
    older.superseded_by_document_id = newer.id


def test_single_document_in_force_is_current_and_initial() -> None:
    doc = _doc("A", date(2023, 6, 1))
    position = evaluate_version_chains([doc], TODAY)[doc.id]
    assert position.is_current and position.is_initial and position.in_force
    assert (position.position, position.chain_length) == (1, 1)
    assert position.supersedes_title is None and position.superseded_by_title is None


def test_two_link_chain_current_is_last() -> None:
    a, b = _doc("Facility", date(2023, 6, 1)), _doc("Amendment 01", date(2025, 3, 15))
    _link(a, b)
    result = evaluate_version_chains([b, a], TODAY)  # order of input must not matter
    assert result[a.id].is_initial and not result[a.id].is_current
    assert result[a.id].superseded_by_title == "Amendment 01"
    assert result[b.id].is_current and not result[b.id].is_initial
    assert result[b.id].supersedes_title == "Facility"
    assert (result[b.id].position, result[b.id].chain_length) == (2, 2)


def test_future_effective_link_is_not_current_yet() -> None:
    a, b = _doc("A", date(2023, 6, 1)), _doc("B", date(2026, 9, 1), effective_date=date(2027, 1, 1))
    _link(a, b)
    result = evaluate_version_chains([a, b], TODAY)
    assert result[a.id].is_current
    assert not result[b.id].is_current and not result[b.id].in_force


def test_expired_document_is_not_in_force() -> None:
    doc = _doc("A", date(2020, 1, 1), expiration_date=date(2025, 12, 31))
    assert not is_in_force(doc, TODAY)
    assert not evaluate_version_chains([doc], TODAY)[doc.id].is_current


def test_hidden_successor_blocks_current() -> None:
    """The successor exists but is not loaded (not allowed): the visible link is not
    current, and only the fact of a successor is exposed."""
    a = _doc("A", date(2023, 6, 1))
    a.superseded_by_document_id = uuid.uuid4()
    position = evaluate_version_chains([a], TODAY)[a.id]
    assert not position.is_current and position.has_successor
    assert position.superseded_by_title is None


def test_hidden_predecessor_means_not_initial() -> None:
    b = _doc("B", date(2025, 1, 1))
    b.supersedes_document_id = uuid.uuid4()
    position = evaluate_version_chains([b], TODAY)[b.id]
    assert position.is_current and not position.is_initial and position.has_predecessor


def test_cycle_does_not_loop_forever() -> None:
    a, b = _doc("A", date(2023, 1, 1)), _doc("B", date(2024, 1, 1))
    _link(a, b)
    _link(b, a)  # corrupt data: A ⇄ B
    result = evaluate_version_chains([a, b], TODAY)
    assert set(result) == {a.id, b.id}
