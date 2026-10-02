"""B-28 two-stage document approval — the pure rules (ADR-024, NOT §5.2).

State machine (code decides every transition, the LLM never does — P-1/5):

    upload by the target department's own department_manager ──▶ approved  [auto_approved]
    upload by anyone else ──▶ pending_metadata
    pending_metadata / changes_requested ──submit (uploader)──▶ pending_review
                                                  (or approved, if the uploader is by now the
                                                   target department's manager)
    pending_review ──approve (target department's manager)──▶ approved
    pending_review ──request_changes (same, comment required)──▶ changes_requested
    approved ──metadata change by anyone but the target manager──▶ pending_review

`management`/`admin` hold no shortcut: they upload like an employee and wait for the target
department's manager (NOT §5.2, Naci 30.09/02.10.2026).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.document import DocumentReviewStatus
from app.models.user import User, UserRole
from app.services.type_family import (
    EXTRA_PREFIX_LITERAL,
    MAX_EXTRA_FIELDS,
    normalize_extra_key,
)

EXTRA_PREFIX = EXTRA_PREFIX_LITERAL

SUBMITTABLE = frozenset(
    {DocumentReviewStatus.pending_metadata, DocumentReviewStatus.changes_requested}
)


def is_target_manager(user: User, department: str | None) -> bool:
    """The one actor who publishes without review and who reviews everyone else: a
    `department_manager` who is a member of the document's department."""
    return (
        department is not None
        and user.role == UserRole.department_manager
        and department in user.department_slugs
    )


def initial_status(user: User, department: str | None) -> DocumentReviewStatus:
    if is_target_manager(user, department):
        return DocumentReviewStatus.approved
    return DocumentReviewStatus.pending_metadata


def status_after_submit(user: User, department: str | None) -> DocumentReviewStatus:
    """Stage 1 done. The uploader may have been given the manager role since uploading —
    then their own confirmation is the approval (same rule as at upload time)."""
    if is_target_manager(user, department):
        return DocumentReviewStatus.approved
    return DocumentReviewStatus.pending_review


def _comparable(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(str(v) for v in value)
    if value is None:
        return None
    return str(value)


@dataclass(frozen=True)
class FieldOutcome:
    field: str
    suggested: Any
    final: Any
    confidence: float | None
    edited: bool  # final differs from the suggestion
    low_confidence: bool  # suggestion below the threshold
    confirmed: bool  # uploader ticked the box


def classify_fields(
    suggestion_fields: dict[str, Any] | None,
    final_values: dict[str, Any],
    confirmed_fields: set[str],
    threshold: float,
) -> list[FieldOutcome]:
    """One outcome per submitted field, against the AI suggestion (if any)."""
    suggestion_fields = suggestion_fields or {}
    outcomes = []
    for field, final in final_values.items():
        guess = suggestion_fields.get(field) or {}
        suggested = guess.get("value")
        confidence = guess.get("confidence")
        has_suggestion = field in suggestion_fields and suggested is not None
        edited = not has_suggestion or _comparable(suggested) != _comparable(final)
        low = has_suggestion and confidence is not None and confidence < threshold
        outcomes.append(
            FieldOutcome(
                field=field,
                suggested=suggested,
                final=final,
                confidence=confidence,
                edited=edited,
                low_confidence=low,
                confirmed=field in confirmed_fields,
            )
        )
    return outcomes


def unconfirmed_low_confidence(outcomes: list[FieldOutcome]) -> list[str]:
    """BACKEND_GAPS §4.7.5: a suggested value under the threshold, kept as suggested, needs an
    explicit confirmation. A changed value is an explicit decision in itself."""
    return [o.field for o in outcomes if o.low_confidence and not o.edited and not o.confirmed]


class ExtraFieldsError(ValueError):
    """Bad extra-field input: unusable key or too many keys (422 at the API)."""


def normalize_extra_updates(raw: dict[str, str | None] | None) -> dict[str, str | None]:
    """Key normalisation for staff/admin input; `None` keeps its meaning (remove the key)."""
    if not raw:
        return {}
    out: dict[str, str | None] = {}
    for key, value in raw.items():
        normalized = normalize_extra_key(key)
        if normalized is None:
            raise ExtraFieldsError(f"invalid key: {key!r}")
        out[normalized] = None if value is None else str(value).strip() or None
    return out


def flatten_suggestion(fields: dict[str, Any] | None) -> dict[str, Any]:
    """Standard fields as they are plus `extra_fields.<key>` entries, so the confidence rule
    runs uniformly over both kinds (B-28b)."""
    if not fields:
        return {}
    flat = {k: v for k, v in fields.items() if k != "extra_fields"}
    for key, guess in (fields.get("extra_fields") or {}).items():
        flat[f"{EXTRA_PREFIX}{key}"] = guess
    return flat


def merge_extra_fields(
    existing: dict[str, Any],
    updates: dict[str, str | None],
    *,
    actor_id: Any,
    suggested: dict[str, Any],
    now_iso: str,
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Apply `updates` to the JSON. Returns (new json, added keys, changed keys). `source` is
    "ai" when the kept value equals Balbal's suggestion, else "user" — the §4.7.3 distinction.
    Caller enforces the key cap error."""
    merged = dict(existing or {})
    added: list[str] = []
    changed: list[str] = []
    for key, value in updates.items():
        before = (merged.get(key) or {}).get("value")
        if value is None:
            if key in merged:
                del merged[key]
                changed.append(key)
            continue
        guess = suggested.get(key) or {}
        from_ai = guess.get("value") is not None and str(guess.get("value")).strip() == value
        if key not in merged and not from_ai:
            added.append(key)
        if before != value:
            changed.append(key)
        merged[key] = {
            "value": value,
            "source": "ai" if from_ai else "user",
            "confidence": guess.get("confidence") if from_ai else None,
            "added_by_id": str(actor_id) if actor_id is not None else None,
            "added_at": now_iso,
        }
    if len(merged) > MAX_EXTRA_FIELDS:
        raise ExtraFieldsError(f"more than {MAX_EXTRA_FIELDS} extra fields")
    return merged, added, changed
