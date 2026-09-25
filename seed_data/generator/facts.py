"""Ledger → formatted placeholder facts per document (docs/plans/PHASE_3_1_PLAN.md §1.1).

Every prose paragraph refers to a number/date/name only through a `[[token]]`
placeholder; this module is the *only* place a ledger value becomes the text that ends
up in a PDF. `generate_documents.py` substitutes tokens into the (frozen, LLM-authored)
prose after it is loaded — the LLM itself never sees a real value (see `generate_prose.py`).

Every `documents[].key_facts` path in the three master ledgers resolves to a scalar
(str/int/float/date) — verified by hand against `seed_data/master/*.yaml` when this
module was written; `validate_ledger.py`'s F8 rule additionally guarantees every path
still resolves after ledger edits.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from seed_data.generator.validate_ledger import LEDGER_FILES, resolve_path

MASTER_DIR = Path(__file__).resolve().parents[1] / "master"

_MONTHS_EN = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)  # fmt: skip

STATUS_LABELS = {
    "tr": {
        "draft": "Taslak",
        "executed": "Yürürlükte",
        "amended": "Tadil Edilmiş",
        "superseded": "Yürürlükten Kaldırılmış (önceki sürüm)",
        "active": "Aktif",
    },
    "en": {
        "draft": "Draft",
        "executed": "Executed",
        "amended": "Amended",
        "superseded": "Superseded (prior version)",
        "active": "Active",
    },
}

# key_facts name -> (kind, unit). "kind" picks the formatter below.
_FIELD_KIND: dict[str, tuple[str, str]] = {
    "capacity_mw": ("number", "MW"),
    "target_capacity_mw": ("number", "MW"),
    "licence_date": ("date", ""),
    "amendment_date": ("date", ""),
    "cod_expected": ("date", ""),
    "cod_actual": ("date", ""),
    "pre_licence_date": ("date", ""),
    "land_acquisition_start": ("date", ""),
    "latest_event": ("date", ""),
    "financial_close_date": ("date", ""),
    "development_start": ("date", ""),
    "cod_deferral_reason": ("text", ""),
    "dscr_covenant": ("ratio", ""),
    "dscr": ("ratio", ""),
    "tenor_years": ("years", ""),
    "grace_months": ("months", ""),
    "total_debt": ("money", ""),
    "local_debt": ("money", ""),
    "eca_debt": ("money", ""),
    "outstanding_debt": ("money", ""),
    "epc_contract_price": ("money", ""),
    "margin_pct": ("percent", ""),
    "mwh": ("mwh", ""),
    "operating_year": ("ordinal", ""),
    "repayment_profile": ("text", ""),
    "approved_spv": ("text", ""),
    "ced_status": ("ced_status", ""),
    # Phase 5.1
    "drawdown_amount": ("money", ""),
    "drawdown_date": ("date", ""),
    "incident_type": ("text", ""),
    "covenant_result": ("text", ""),
    "availability_pct": ("percent", ""),
    "ghi_share_pct": ("percent", ""),
}

_PREFIX_TO_LEDGER = {"ANK": "ankara_res", "IZM": "izmir_res", "CO": "company"}


def load_raws(master_dir: Path = MASTER_DIR) -> dict[str, dict[str, Any]]:
    return {
        name: yaml.safe_load((master_dir / filename).read_text(encoding="utf-8"))
        for name, filename in LEDGER_FILES.items()
    }


def format_date(value: date, language: str) -> str:
    if language == "tr":
        return f"{value.day:02d}.{value.month:02d}.{value.year}"
    return f"{_MONTHS_EN[value.month - 1]} {value.day}, {value.year}"


def _format_money(value: float, language: str, currency: str = "EUR") -> str:
    amount = int(round(value))
    grouped = f"{amount:,}"
    if language == "tr":
        grouped = grouped.replace(",", ".")
    return f"{grouped} {currency}"


def format_percent(value: float, language: str) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"%{text.replace('.', ',')}" if language == "tr" else f"{text}%"


def _format_ratio(value: float, language: str) -> str:
    text = f"{value:.2f}"
    if language == "tr":
        text = text.replace(".", ",")
    return f"{text}x"


def _format_number(value: float, language: str, unit: str) -> str:
    text = str(int(value)) if float(value).is_integer() else f"{value:.1f}"
    if language == "tr":
        text = text.replace(".", ",")
    return f"{text} {unit}".strip()


def _format_years(value: float, language: str) -> str:
    n = int(value)
    return f"{n} yıl" if language == "tr" else f"{n} years"


def _format_months(value: float, language: str) -> str:
    n = int(value)
    return f"{n} ay" if language == "tr" else f"{n} months"


def _format_ordinal(value: float, language: str) -> str:
    n = int(value)
    return f"{n}." if language == "tr" else f"{n}{_ordinal_suffix_en(n)}"


def _ordinal_suffix_en(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _format_ced_status(value: str, language: str) -> str:
    if value == "ongoing":
        return "devam ediyor" if language == "tr" else "ongoing"
    return str(value)


def format_value(field_name: str, value: Any, language: str) -> str:
    """Format a resolved `key_facts` scalar for prose substitution."""
    kind, unit = _FIELD_KIND.get(field_name, ("text", ""))
    if kind == "date":
        if not isinstance(value, date):
            raise TypeError(f"{field_name}: expected a date, got {value!r}")
        return format_date(value, language)
    if kind == "money":
        return _format_money(float(value), language)
    if kind == "percent":
        return format_percent(float(value), language)
    if kind == "ratio":
        return _format_ratio(float(value), language)
    if kind == "number":
        return _format_number(float(value), language, unit)
    if kind == "years":
        return _format_years(float(value), language)
    if kind == "months":
        return _format_months(float(value), language)
    if kind == "mwh":
        return _format_number(float(value), language, "MWh")
    if kind == "ordinal":
        return _format_ordinal(float(value), language)
    if kind == "ced_status":
        return _format_ced_status(str(value), language)
    return str(value)


def guess_field_kind(path: str) -> str | None:
    """Best-effort reverse lookup: does `path` (a ledger path, e.g.
    `"project.finance.outstanding_debt_as_of_demo_today.value"`) contain one of the known
    `_FIELD_KIND` keys? Longest key wins on overlap (`"dscr_covenant"` over `"dscr"`).
    Used by `scripts/eval_lib.py` (Phase 4.1) to format a resolved ledger value the same
    way `build_facts()` would format it inside a generated document."""
    matches = [key for key in _FIELD_KIND if key in path]
    return max(matches, key=len) if matches else None


def format_ledger_leaf(path: str, value: Any, parent: Any, language: str) -> str | None:
    """Format a resolved ledger leaf as it would appear in a generated document, or
    `None` if `path` doesn't match a known field kind (Phase 4.1's eval runner then skips
    the value check for that question rather than guessing a format). `parent` is the
    dict enclosing `value` (if any) — used only for money's sibling `currency` key, since
    `format_value()` alone always assumes EUR."""
    field_name = guess_field_kind(path)
    if field_name is None:
        return None
    kind, _unit = _FIELD_KIND[field_name]
    if kind == "money" and isinstance(parent, dict) and "currency" in parent:
        return _format_money(float(value), language, str(parent["currency"]))
    return format_value(field_name, value, language)


def _ledger_key_for_doc_id(doc_id: str) -> str:
    prefix = doc_id.split("-")[1]
    return _PREFIX_TO_LEDGER[prefix]


def _project_name(doc_id: str) -> str | None:
    prefix = doc_id.split("-")[1]
    return {"ANK": "Ankara RES", "IZM": "İzmir RES", "CO": None}[prefix]


def _spv_name(doc_id: str, raws: dict[str, Any]) -> str:
    ledger_key = _ledger_key_for_doc_id(doc_id)
    if ledger_key == "company":
        return str(raws["company"]["holding"]["name"]["value"])
    return str(raws[ledger_key]["project"]["spv"]["name"]["value"])


def build_facts(doc: dict[str, Any], raws: dict[str, Any]) -> dict[str, str]:
    """Standard cover/meta facts plus every `key_facts` entry, all pre-formatted."""
    language = doc["language"]
    doc_id = doc["id"]
    ledger_key = _ledger_key_for_doc_id(doc_id)
    spv_name = _spv_name(doc_id, raws)
    other_parties = [p for p in doc["parties"] if p != spv_name]

    facts: dict[str, str] = {
        "language": language,
        "title": str(doc["name"]["value"]),
        "document_no": doc_id,
        "version_label": doc["version"],
        "status_label": STATUS_LABELS[language][doc["status"]],
        "document_date": format_date(doc["document_date"]["value"], language),
        "spv_name": spv_name,
        "counterparty": other_parties[0] if other_parties else spv_name,
        "parties_list": ", ".join(doc["parties"]),
    }
    project_name = _project_name(doc_id)
    if project_name:
        facts["project_name"] = project_name

    effective = doc.get("effective_date")
    facts["effective_date"] = (
        format_date(effective["value"], language)
        if effective is not None
        else (
            "yürürlük tarihi henüz belirlenmedi"
            if language == "tr"
            else "effective date not yet set"
        )
    )

    for field_name, path in doc.get("key_facts", {}).items():
        raw_value = resolve_path(raws[ledger_key], path)
        facts[field_name] = format_value(field_name, raw_value, language)

    return facts
