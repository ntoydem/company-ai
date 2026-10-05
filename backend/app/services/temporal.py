"""The system's single notion of "today" (ADR-026) and the date arithmetic built on it.

`Settings.demo_today` and `Settings.company_timezone` are read **only** here — every other
module asks `today(settings)`. This is what lets the demo calendar (`DEMO_MODE=true`,
default) and a customer's real calendar (`DEMO_MODE=false`) be the same code path: rule 5
(TEMPORAL TRUTH) does not care which one is live, only that there is exactly one.

Rule 3 (CALCULATION) extended to dates: "how many days left" / "has this expired" is
arithmetic, so it is computed here in Python, never asked of the LLM (previously rule 8 of
`answer_prompt.SYSTEM_PROMPT` told the model to do this itself from the `BUGÜN` line)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.models.document import Document


def today(settings: Settings) -> date:
    """The system's current date — demo (`settings.demo_today`) or real, never both."""
    if settings.demo_mode_enabled:
        return settings.demo_today
    return datetime.now(ZoneInfo(settings.company_timezone)).date()


def _plural(n: int, unit: str) -> str:
    return f"{n} {unit}"


def _tr_duration(days: int) -> str:
    """`gün`/`ay`/`yıl` ile kaba bir süre ifadesi — GG.AA.YYYY'nin yanında okunabilir bağlam
    (ADR-026 §2); kesin hesap her zaman gün sayısından (`days`), bu yalnızca biçim."""
    if days < 60:
        return _plural(days, "gün")
    months = round(days / 30.4368)  # ortalama ay uzunluğu
    if months < 18:
        return _plural(months, "ay")
    years, remaining_months = divmod(months, 12)
    if remaining_months == 0:
        return _plural(years, "yıl")
    return f"{_plural(years, 'yıl')} {_plural(remaining_months, 'ay')}"


def expiration_note(document: Document, today_: date) -> str | None:
    """A ready-made, code-computed sentence for `format_source()` — `None` when the document
    carries no `expiration_date` (older sources stay byte-identical, same pattern as
    `describe_metadata`). The model reads this line; it never computes the difference
    itself (rule 3/8, ADR-026)."""
    expiration = document.expiration_date
    if expiration is None:
        return None
    delta = (expiration - today_).days
    expiration_str = expiration.strftime("%d.%m.%Y")
    if delta >= 0:
        return f"Süre: {expiration_str} tarihine kadar yürürlükte ({_tr_duration(delta)} kaldı)"
    return f"Süre: {expiration_str} tarihinde sona erdi ({_tr_duration(-delta)} önce)"
