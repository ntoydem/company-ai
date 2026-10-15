"""`scripts.run_eval.VisibilityIndex` (İş Emri 2026-10-15F0 A2) — the G3 visibility set is
resolved per `ask_as_user` through the injected gate lookup, for *any* user the question set
names, with no static user list. Pure: a fake session factory and a fake lookup, no DB."""

from __future__ import annotations

from contextlib import nullcontext
from uuid import UUID, uuid4

import pytest

from scripts.run_eval import VisibilityIndex

_FINANCIAL_MODEL = uuid4()
_FA = uuid4()
_RULES: dict[str, set[UUID]] = {
    "finans": {_FA},
    "finans_mudur": {_FA, _FINANCIAL_MODEL},  # the user the old static list left out
    "enerji": set(),
}


def _index() -> tuple[VisibilityIndex, list[str]]:
    calls: list[str] = []

    def lookup(session: object, username: str) -> set[UUID] | None:
        calls.append(username)
        return _RULES.get(username)

    return VisibilityIndex(lambda: nullcontext(object()), lookup=lookup), calls


def test_every_named_user_is_resolved_through_the_gate() -> None:
    index, _ = _index()
    assert index.for_user("finans_mudur") == {str(_FA), str(_FINANCIAL_MODEL)}
    assert index.for_user("finans") == {str(_FA)}
    assert index.for_user("enerji") == frozenset()
    assert index.resolved == {"enerji": 0, "finans": 1, "finans_mudur": 2}


def test_lookup_is_cached_per_user() -> None:
    index, calls = _index()
    index.for_user("finans_mudur")
    index.for_user("finans_mudur")
    index.for_user("finans")
    assert calls == ["finans_mudur", "finans"]


def test_unknown_user_is_an_error_not_an_empty_set() -> None:
    """An empty set would flag every shown document as unauthorised (the S3 §3.2 B false
    positive, the other way round); a missing demo user must stop the run instead."""
    index, _ = _index()
    with pytest.raises(LookupError, match="demo user missing"):
        index.for_user("misafir")
