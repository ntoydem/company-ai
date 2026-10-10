"""`app.services.temporal` (ADR-026): the one place `Settings.demo_today`/`company_timezone`
are read, and the date arithmetic moved out of the LLM prompt (rule 3/8)."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.core.config import Settings
from app.models.document import Document, DocumentStatus
from app.services import temporal


def test_demo_mode_on_returns_demo_today(settings: Settings) -> None:
    assert settings.demo_mode_enabled is True
    assert temporal.today(settings) == date(2026, 10, 6)


def test_demo_mode_off_returns_the_real_day_in_company_timezone(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    off = settings.model_copy(
        update={"demo_mode_enabled": False, "company_timezone": "Europe/Istanbul"}
    )

    class _FixedClock:
        @staticmethod
        def now(tz: object) -> datetime:
            # 00:30 Istanbul (UTC+3) on 02.01.2027 — a UTC-naive "today" would still say
            # 01.01.2027, which is exactly the bug a shared, tz-aware clock avoids.
            return datetime(2027, 1, 2, 0, 30, tzinfo=tz)  # type: ignore[arg-type]

    monkeypatch.setattr(temporal, "datetime", _FixedClock)
    assert temporal.today(off) == date(2027, 1, 2)


def _document(**overrides: object) -> Document:
    base = dict(
        title="Test",
        document_type="Insurance Notice",
        document_date=date(2024, 1, 10),
        counterparty="STU Sigorta",
        status=DocumentStatus.executed,
        tags=[],
        effective_date=date(2024, 1, 10),
        expiration_date=None,
    )
    base.update(overrides)
    return Document(**base)  # type: ignore[arg-type]


def test_expiration_note_is_none_without_an_expiration_date() -> None:
    assert temporal.expiration_note(_document(), date(2026, 9, 15)) is None


def test_expiration_note_counts_days_remaining() -> None:
    document = _document(expiration_date=date(2026, 9, 20))
    note = temporal.expiration_note(document, date(2026, 9, 15))
    assert note == "Süre: 20.09.2026 tarihine kadar yürürlükte (5 gün kaldı)"


def test_expiration_note_counts_time_since_it_expired() -> None:
    document = _document(expiration_date=date(2025, 1, 9))
    note = temporal.expiration_note(document, date(2026, 9, 15))
    assert note == "Süre: 09.01.2025 tarihinde sona erdi (1 yıl 8 ay önce)"
