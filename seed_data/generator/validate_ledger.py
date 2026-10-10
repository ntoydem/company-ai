"""Truth ledger validator (PHASES.md Phase 2.1, ADR-013, docs/plans/PHASE_2_1_PLAN.md §3).

    python -m seed_data.generator.validate_ledger [--master DIR] [--questions FILE] [--summary]

One finding per line (`ERROR <file> <path>: <message>` / `WARNING ...`), then
`N error(s), M warning(s)`. Exit code 0 only when N == 0. Structural errors come from
the Pydantic schema (`ledger_schema.py`); everything else here is a cross-field rule.
Runs inside the backend container; never imported by `app/`.
"""

from __future__ import annotations

import argparse
import calendar
import json
import math
import os
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from seed_data.generator import debt_math
from seed_data.generator import ledger_schema as ls

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER = REPO_ROOT / "seed_data" / "master"
DEFAULT_QUESTIONS = REPO_ROOT / "seed_data" / "evaluation" / "questions.json"

LEDGER_FILES = {
    "company": "company.yaml",
    "ankara_res": "ankara_res.yaml",
    "izmir_res": "izmir_res.yaml",
    "fx_rates": "fx_rates.yaml",
    # Adım 5 Aşama C (10.10.2026): 5 new SPVs, manually added (Aşama B SORU 3 — not
    # derived from company.yaml, kept in sync by a dedicated test instead).
    "yesilova_res": "yesilova_res.yaml",
    "boztepe_res": "boztepe_res.yaml",
    "gunesalan_ges": "gunesalan_ges.yaml",
    "akyar_ges": "akyar_ges.yaml",
    "demirci_res": "demirci_res.yaml",
}
PROJECT_PREFIX = {
    "ankara_res": "ANK",
    "izmir_res": "IZM",
    "company": "CO",
    "yesilova_res": "YSV",
    "boztepe_res": "BOZ",
    "gunesalan_ges": "GNS",
    "akyar_ges": "AKY",
    "demirci_res": "DMR",
}
# Adım 5 Aşama C: maps each `company.yaml` SPV registry code to its raw-ledger key —
# the sync test (`test_project_prefix_matches_company_spv_registry`) checks this against
# `company.yaml`'s own `spvs` list so the two can never silently drift apart.
PROJECT_CODE_TO_RAW_KEY = {
    "ANK_RES": "ankara_res",
    "IZM_RES": "izmir_res",
    "YSV_RES": "yesilova_res",
    "BOZ_RES": "boztepe_res",
    "GNS_GES": "gunesalan_ges",
    "AKY_GES": "akyar_ges",
    "DMR_RES": "demirci_res",
}
# Adım 5 Aşama C (10.10.2026): any parsed ledger model, Ankara/İzmir/company's original
# three or one of the two new shared shapes (ADIM5_ASAMA_C_PLAN.md §2.2).
LedgerModel = (
    ls.AnkaraLedger
    | ls.IzmirLedger
    | ls.CompanyLedger
    | ls.OperatingLedger
    | ls.GenericDevelopmentLedger
)
IZMIR_POST_LICENCE_KEYS = (
    "licence",
    "financing_signed",
    "financial_close",
    "epc_signed",
    "construction_start",
    "construction_end",
    "commissioning",
    "cod_expected_initial",
    "cod_actual",
    "operation_start",
)
QUOTAS = {"Kızılova RES": 12, "Karatepe RES": 35}
CATEGORY_QUOTAS = {
    "hallucination": 3,
    "isolation": 3,
    "authorization": 3,
    "comparison": 3,
    "ambiguous": 3,
    "term_mismatch": 3,
}
MIN_QUESTIONS = 60
FX_CROSS_TOLERANCE = 0.02
# "<Name> A.Ş." style company suffixes; every match must be whitelisted (SPEC_05 §11).
_NAME_PATTERN = re.compile(
    r"([A-ZÇĞİÖŞÜ][\w'’.-]*(?:\s+[A-ZÇĞİÖŞÜ][\w'’.-]*){0,4}\s+"
    r"(?:A\.Ş\.|Ltd\.(?:\s*Şti\.)?|Bank|Sigorta|GmbH|S\.A\.|Inc\.))"
)
_PATH_TOKEN = re.compile(r"([^.\[\]]+)|\[(-?\d+)\]")


@dataclass
class Issue:
    level: str
    file: str
    path: str
    message: str

    def render(self) -> str:
        return f"{self.level} {self.file} {self.path}: {self.message}"


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, file: str, path: str, message: str) -> None:
        self.issues.append(Issue("ERROR", file, path, message))

    def warning(self, file: str, path: str, message: str) -> None:
        self.issues.append(Issue("WARNING", file, path, message))

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "WARNING")


# ---------------------------------------------------------------- helpers


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_model[M: BaseModel](model: type[M], data: Any, file: str, report: Report) -> M | None:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            loc = ".".join(str(part) for part in error["loc"]) or "<root>"
            report.error(file, loc, error["msg"])
        return None


def resolve_path(root: Any, path: str) -> Any:
    """`project.finance.drawdowns[0].amount.value`; raises KeyError/IndexError/TypeError."""
    node = root
    for match in _PATH_TOKEN.finditer(path):
        key, index = match.group(1), match.group(2)
        node = node[int(index)] if index is not None else node[key]
    return node


def string_leaves(node: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from string_leaves(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from string_leaves(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def count_tags(node: Any) -> dict[str, int]:
    counts = {"USER_FACT": 0, "AI_ASSUMPTION": 0}
    if isinstance(node, dict):
        tag = node.get("tag")
        if tag in counts:
            counts[tag] += 1
        for value in node.values():
            for key, n in count_tags(value).items():
                counts[key] += n
    elif isinstance(node, list):
        for value in node:
            for key, n in count_tags(value).items():
                counts[key] += n
    return counts


def find_conflict_groups(
    node: Any, file: str, path: str = ""
) -> dict[str, list[tuple[str, str, bool, str | None]]]:
    """Adım 5 (09.10.2026): every `conflict_group` tag found anywhere in a raw ledger dict,
    with where it was found, whether `deliberate_conflict` was set alongside it, and its
    `conflict_kind` (İş 4a). Walks the *raw* YAML (same style as `count_tags`), so it works
    uniformly across every ledger file without per-schema special-casing."""
    groups: dict[str, list[tuple[str, str, bool, str | None]]] = {}
    if isinstance(node, dict):
        group = node.get("conflict_group")
        if isinstance(group, str):
            groups.setdefault(group, []).append(
                (
                    file,
                    path or "<root>",
                    bool(node.get("deliberate_conflict")),
                    node.get("conflict_kind"),
                )
            )
        for key, value in node.items():
            for g, entries in find_conflict_groups(
                value, file, f"{path}.{key}" if path else key
            ).items():
                groups.setdefault(g, []).extend(entries)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            for g, entries in find_conflict_groups(value, file, f"{path}[{i}]").items():
                groups.setdefault(g, []).extend(entries)
    return groups


def check_conflict_groups(raws: dict[str, dict[str, Any]], report: Report) -> None:
    """C1 (Adım 5): a `conflict_group` name must be used on at least two values (a group of
    one marks nothing) and every member of a group must carry `deliberate_conflict: true` —
    a value in a group without the flag is either a typo'd group name or a forgotten flag,
    both worth a hard error rather than silently passing. İş 4a: every member of a group
    must also carry the same `conflict_kind` (missing, or disagreeing with the rest of the
    group, is an error — a group is one kind of trap, not a mix)."""
    all_groups: dict[str, list[tuple[str, str, bool, str | None]]] = {}
    for name, raw in raws.items():
        filename = LEDGER_FILES.get(name, name)
        for group, entries in find_conflict_groups(raw, filename).items():
            all_groups.setdefault(group, []).extend(entries)
    for group, entries in all_groups.items():
        if len(entries) < 2:
            file, path, _, _ = entries[0]
            report.error(
                file, path, f"C1: conflict_group {group!r} has only one member — tag or group name?"
            )
            continue
        for file, path, flagged, _ in entries:
            if not flagged:
                report.error(
                    file,
                    path,
                    f"C1: conflict_group {group!r} member missing deliberate_conflict: true",
                )
        kinds = {kind for _, _, _, kind in entries}
        if len(kinds) > 1:
            for file, path, _, kind in entries:
                report.error(
                    file,
                    path,
                    f"C1: conflict_group {group!r} has mismatched conflict_kind "
                    f"({kind!r}) — every member must share one kind",
                )
        elif None in kinds:
            file, path, _, _ = entries[0]
            report.error(file, path, f"C1: conflict_group {group!r} member missing conflict_kind")


def quarter_end(period: str) -> date:
    quarter, year = period.split("_")
    month = int(quarter[1]) * 3
    return date(int(year), month, calendar.monthrange(int(year), month)[1])


def month_end(month: str) -> date:
    year, mon = (int(part) for part in month.split("-"))
    return date(year, mon, calendar.monthrange(year, mon)[1])


def operating_year(demo_today: date, cod: date) -> int:
    """Anniversary-based: the first operating year runs from COD to the day before its
    first anniversary (docs/plans/PHASE_2_1_PLAN.md T10)."""
    return math.floor((demo_today - cod).days / 365.25) + 1


def fact_date(fact: ls.Fact | None) -> date | None:
    if fact is None:
        return None
    return fact.value if isinstance(fact.value, date) else None


# ---------------------------------------------------------------- rule sets


def check_chronology(ankara: ls.AnkaraLedger, report: Report) -> None:
    f = "ankara_res.yaml"
    t = ankara.project.timeline
    demo_today = ankara.meta.demo_today

    def d(name: str) -> date | None:
        event: ls.Event = getattr(t, name)
        if event.date is None:
            report.error(f, f"project.timeline.{name}.date", "Ankara timeline dates must be set")
        return event.date

    order = [
        "development_start",
        "licence",
        "financing_signed",
        "financial_close",
        "construction_start",
        "commissioning",
        "cod_actual",
    ]
    dates = {name: d(name) for name in order}
    for earlier, later in zip(order, order[1:], strict=False):
        a, b = dates[earlier], dates[later]
        if a is not None and b is not None and not a < b:
            report.error(f, f"project.timeline.{later}.date", f"C1: must be after {earlier}")

    cod = dates["cod_actual"]
    operation_start = d("operation_start")
    if cod and operation_start and operation_start < cod:
        report.error(f, "project.timeline.operation_start.date", "C1: must be >= cod_actual")

    epc, construction_end, licence = d("epc_signed"), d("construction_end"), dates["licence"]
    if epc and construction_end and epc > construction_end:
        report.error(f, "project.timeline.epc_signed.date", "C2: EPC signed after construction end")
    if epc and licence and epc < licence:
        report.error(f, "project.timeline.epc_signed.date", "C2: EPC signed before licence")
    construction_start = dates["construction_start"]
    if construction_start and construction_end and construction_end <= construction_start:
        report.error(f, "project.timeline.construction_end.date", "C1: must be after start")

    financial_close = dates["financial_close"]
    drawdowns = ankara.project.finance.drawdowns
    if financial_close and drawdowns:
        first = min(x.date for x in drawdowns)
        if first < financial_close:
            report.error(
                f, "project.finance.drawdowns", "C3: first drawdown before financial close"
            )

    licence_amendment = d("licence_amendment")
    if licence and licence_amendment and licence_amendment <= licence:
        report.error(f, "project.timeline.licence_amendment.date", "C4: must be after licence")

    cod_expected = d("cod_expected_initial")
    if cod and cod_expected and cod != cod_expected:
        subjects = [co.subject.value for co in ankara.project.construction.change_orders]
        if not any("cod" in str(s).lower() for s in subjects):
            report.warning(
                f, "project.construction.change_orders", "C5: COD moved but no COD change order"
            )

    if cod:
        computed = operating_year(demo_today, cod)
        declared = ankara.project.operations.operating_year_on_demo_today.value
        if declared != computed:
            report.error(
                f,
                "project.operations.operating_year_on_demo_today.value",
                f"C6: declared {declared!r}, computed {computed} from cod_actual and demo_today",
            )
        if computed != 3:
            report.error(
                f, "project.timeline.cod_actual.date", f"C6: operating year is {computed}, not 3"
            )

    fin = ankara.project.finance
    for i, test in enumerate(fin.covenant_tests):
        if quarter_end(test.period) > demo_today:
            report.error(f, f"project.finance.covenant_tests[{i}].period", "C7: after demo_today")
    for i, row in enumerate(ankara.project.operations.monthly_production):
        if month_end(row.month) > demo_today:
            report.error(
                f, f"project.operations.monthly_production[{i}].month", "C7: after demo_today"
            )
    for i, dd in enumerate(fin.drawdowns):
        if dd.date > demo_today:
            report.error(f, f"project.finance.drawdowns[{i}].date", "C7: after demo_today")


def check_izmir_timeline(izmir: ls.IzmirLedger, report: Report) -> None:
    f = "izmir_res.yaml"
    t = izmir.project.timeline
    order = [
        "development_start",
        "pre_licence_application",
        "pre_licence",
        "land_acquisition_start",
        "ced_application",
    ]
    previous: tuple[str, date] | None = None
    for name in order:
        event: ls.Event = getattr(t, name)
        if event.date is None:
            continue
        if previous and event.date < previous[1]:
            report.error(f, f"project.timeline.{name}.date", f"C9: before {previous[0]}")
        previous = (name, event.date)
    demo_today = izmir.meta.demo_today
    dated: list[date] = [getattr(t, n).date for n in order if getattr(t, n).date is not None]
    for i, permit in enumerate(izmir.project.development.permits_completed):
        if permit.date > demo_today:
            report.error(
                f, f"project.development.permits_completed[{i}].date", "C9: after demo_today"
            )
        dated.append(permit.date)
    latest = izmir.project.development.latest_event.date
    if latest is None:
        report.error(f, "project.development.latest_event.date", "C9: latest_event needs a date")
    elif dated and latest < max(dated):
        report.error(
            f, "project.development.latest_event.date", "C9: an older date than other events"
        )
    elif latest > demo_today:
        report.error(f, "project.development.latest_event.date", "C9: after demo_today")


def check_document_dates(
    file: str, docs: list[ls.Document], demo_today: date, report: Report
) -> None:
    by_id = {doc.id: doc for doc in docs}
    for i, doc in enumerate(docs):
        doc_date = fact_date(doc.document_date)
        if doc_date is None:
            report.error(file, f"documents[{i}].document_date.value", "C8: must be a date")
            continue
        if doc_date > demo_today:
            report.error(file, f"documents[{i}].document_date.value", "C8: after demo_today")
        effective = fact_date(doc.effective_date)
        if doc.effective_date is not None and effective is None:
            report.error(file, f"documents[{i}].effective_date.value", "C8: must be a date or null")
        if effective and effective < doc_date:
            report.error(file, f"documents[{i}].effective_date.value", "C8: before document_date")
        # ADR-026: a document's validity end, when it has one — must postdate whichever of
        # effective_date/document_date marks it starting, so "doldu mu" is never ambiguous.
        expiration = fact_date(doc.expiration_date)
        if doc.expiration_date is not None and expiration is None:
            report.error(
                file, f"documents[{i}].expiration_date.value", "C11: must be a date or null"
            )
        if expiration:
            starts = effective or doc_date
            if expiration <= starts:
                report.error(
                    file,
                    f"documents[{i}].expiration_date.value",
                    "C11: must be after effective_date/document_date",
                )
        if doc.supersedes and doc.supersedes in by_id:
            older = fact_date(by_id[doc.supersedes].document_date)
            if older and doc_date <= older:
                report.error(
                    file,
                    f"documents[{i}].document_date.value",
                    "C8: not after the document it supersedes",
                )


def check_debt_schedule(ankara: ls.AnkaraLedger, report: Report) -> None:
    """F9-F11 (Phase 4.2): the Financial Model inputs must reproduce the approved facts.
    F9 balance after the last half-year closed before demo_today == outstanding_debt;
    F10 cfads / quarterly debt service == covenant_tests.dscr (±0.01);
    F11 instalments sum to the drawn amount and end within the current tenor."""
    f = "ankara_res.yaml"
    fin = ankara.project.finance
    if not (fin.base_rate_pct_by_year and fin.repayment_schedule and fin.cfads_by_quarter):
        report.error(f, "project.finance", "F9: base rates, repayment schedule and cfads required")
        return
    rows = debt_math.build_schedule(
        drawdowns=[(d.date, float(d.amount.value)) for d in fin.drawdowns],
        instalments=[(i.date, float(i.principal.value)) for i in fin.repayment_schedule],
        base_rate_pct_by_year={b.year: b.rate_pct for b in fin.base_rate_pct_by_year},
        margin_pct=float(fin.interest.margin_pct.current.value),  # type: ignore[arg-type]
    )
    outstanding = debt_math.outstanding_on(rows, ankara.meta.demo_today)
    if abs(outstanding - float(fin.outstanding_debt_as_of_demo_today.value)) > 0.5:
        report.error(
            f,
            "project.finance.repayment_schedule",
            f"F9: balance on demo_today {outstanding:.0f} != outstanding_debt "
            f"{fin.outstanding_debt_as_of_demo_today.value}",
        )
    cfads = {c.period: float(c.cfads.value) for c in fin.cfads_by_quarter}
    for test in fin.covenant_tests:
        if test.period not in cfads:
            report.error(f, "project.finance.cfads_by_quarter", f"F10: no cfads for {test.period}")
            continue
        service = debt_math.quarterly_debt_service(rows, test.period)
        if abs(cfads[test.period] / service - test.dscr) > 0.01:
            report.error(
                f,
                "project.finance.cfads_by_quarter",
                f"F10: {test.period} cfads/service = {cfads[test.period] / service:.3f}, "
                f"covenant test says {test.dscr}",
            )
    drawn = sum(float(d.amount.value) for d in fin.drawdowns)
    repaid = sum(float(i.principal.value) for i in fin.repayment_schedule)
    if abs(drawn - repaid) > 0.5:
        report.error(
            f,
            "project.finance.repayment_schedule",
            f"F11: instalments {repaid:.0f} != drawn {drawn:.0f}",
        )
    close = ankara.project.timeline.financial_close.date
    last = max(i.date for i in fin.repayment_schedule)
    tenor_years = int(fin.tenor_years.current.value)  # type: ignore[arg-type]
    if close is not None and last > close.replace(year=close.year + tenor_years):
        report.error(f, "project.finance.repayment_schedule", "F11: last instalment beyond tenor")


def check_finance(ankara: ls.AnkaraLedger, report: Report) -> None:
    f = "ankara_res.yaml"
    fin = ankara.project.finance
    monies = {
        "capex": fin.capex,
        "equity": fin.equity,
        "total_debt": fin.total_debt,
        "local_debt": fin.local_debt,
        "eca_debt": fin.eca_debt,
        "outstanding_debt_as_of_demo_today": fin.outstanding_debt_as_of_demo_today,
    }
    currencies = {m.currency for m in monies.values()}
    if len(currencies) != 1:
        report.error(f, "project.finance", f"F1/F2: mixed currencies {sorted(currencies)}")
    if fin.local_debt.value + fin.eca_debt.value != fin.total_debt.value:
        report.error(
            f, "project.finance.total_debt.value", "F1: local_debt + eca_debt != total_debt"
        )
    if fin.total_debt.value + fin.equity.value != fin.capex.value:
        report.error(f, "project.finance.capex.value", "F2: total_debt + equity != capex")
    drawn = sum(dd.amount.value for dd in fin.drawdowns)
    if any(dd.amount.currency != fin.total_debt.currency for dd in fin.drawdowns):
        report.error(
            f, "project.finance.drawdowns", "F3: drawdown currency differs from total_debt"
        )
    if drawn > fin.total_debt.value:
        report.error(f, "project.finance.drawdowns", "F3: drawdowns exceed total_debt")
    if fin.outstanding_debt_as_of_demo_today.value > drawn:
        report.error(
            f, "project.finance.outstanding_debt_as_of_demo_today.value", "F3: exceeds drawn amount"
        )

    tenor, dscr = fin.tenor_years, fin.dscr_covenant
    if float(tenor.current.value) < float(tenor.initial.value):  # type: ignore[arg-type]
        report.error(
            f, "project.finance.tenor_years.current.value", "F4: tenor shortened (spec: extended)"
        )
    if float(dscr.current.value) > float(dscr.initial.value):  # type: ignore[arg-type]
        report.error(
            f,
            "project.finance.dscr_covenant.current.value",
            "F4: covenant tightened (spec: relaxed)",
        )
    check_debt_schedule(ankara, report)

    by_id = {doc.id: doc for doc in ankara.documents}
    for name, changed in (("tenor_years", tenor), ("dscr_covenant", dscr)):
        doc = by_id.get(changed.changed_by)
        if doc is None or not doc.version.startswith("AMD"):
            report.error(
                f, f"project.finance.{name}.changed_by", "F4: must reference an AMD* chain document"
            )

    amd = by_id.get(dscr.changed_by)
    effective = fact_date(amd.effective_date) if amd else None
    for i, test in enumerate(fin.covenant_tests):
        if effective is None:
            break
        threshold = (
            float(dscr.initial.value)
            if quarter_end(test.period) < effective
            else float(dscr.current.value)
        )  # type: ignore[arg-type]
        expected = "pass" if test.dscr >= threshold else "fail"
        if test.result != expected:
            report.error(
                f,
                f"project.finance.covenant_tests[{i}].result",
                f"F5: dscr {test.dscr} vs covenant {threshold} => {expected}",
            )

    chain = fin.facility_chain
    if [by_id[i].version if i in by_id else None for i in chain] != list(
        ls.FACILITY_CHAIN_VERSIONS
    ):
        report.error(
            f,
            "project.finance.facility_chain",
            f"F6: expected versions {list(ls.FACILITY_CHAIN_VERSIONS)}",
        )
    else:
        docs = [by_id[i] for i in chain]
        for older, newer in zip(docs, docs[1:], strict=False):
            if older.superseded_by != newer.id or newer.supersedes != older.id:
                report.error(
                    f,
                    "project.finance.facility_chain",
                    f"F6: link {older.id} -> {newer.id} not wired",
                )
        if docs[0].supersedes is not None or docs[-1].superseded_by is not None:
            report.error(f, "project.finance.facility_chain", "F6: chain must start and end open")
        current = [d.id for d in docs if d.status in ("executed", "active")]
        if current != [docs[-1].id]:
            report.error(
                f,
                "project.finance.facility_chain",
                f"F6: exactly the last link must be current, got {current}",
            )
        for d in docs:
            if d.type != "Facility Agreement":
                report.error(
                    f, "project.finance.facility_chain", f"F6: {d.id} is not a Facility Agreement"
                )

    epc_doc = by_id.get(ankara.project.construction.epc_contract_current_doc)
    if epc_doc is None or "EPC" not in epc_doc.type:
        report.error(
            f, "project.construction.epc_contract_current_doc", "F7: must reference an EPC document"
        )

    for i, row in enumerate(ankara.project.operations.budget_vs_actual):
        if row.budget.currency != "TRY" or row.actual.currency != "TRY":
            report.warning(
                f, f"project.operations.budget_vs_actual[{i}]", "M2: budgets are TRY by decision"
            )
    for name, money in monies.items():
        if money.currency != "EUR":
            report.warning(
                f, f"project.finance.{name}.currency", "M2: loan amounts are EUR by decision"
            )
    if ankara.project.construction.epc_contract_price.currency != "EUR":
        report.warning(
            f,
            "project.construction.epc_contract_price.currency",
            "M2: EPC price is EUR by decision",
        )


def check_izmir_isolation(
    izmir_raw: dict[str, Any], izmir: ls.IzmirLedger | None, report: Report
) -> None:
    f = "izmir_res.yaml"
    project = izmir_raw.get("project", {})
    timeline = project.get("timeline", {})
    for key in IZMIR_POST_LICENCE_KEYS:
        if timeline.get(key) is not None:
            report.error(
                f, f"project.timeline.{key}", "I1: must be null (İzmir has no licence yet)"
            )
    for key in ("finance", "construction", "operations", "turbines"):
        if project.get(key) is not None:
            report.error(f, f"project.{key}", "I1: must be null (İzmir has no licence yet)")
    if izmir is None:
        return
    for i, doc in enumerate(izmir.documents):
        if doc.type in ls.FINANCE_DOCUMENT_TYPES:
            report.error(f, f"documents[{i}].type", "I2: İzmir has no finance documents")


def check_cross_project_refs(raws: dict[str, dict[str, Any]], report: Report) -> None:
    """Adım 5 Aşama C (10.10.2026): generalized from a hardcoded Ankara<->İzmir pair to
    every registered project (N-way) — a project's raw file must never reference any
    *other* project's raw-file key or `DOC-<prefix>-` id, however many there are."""
    project_names = [name for name in PROJECT_PREFIX if name != "company" and name in raws]
    for name in project_names:
        others = [other for other in project_names if other != name]
        for path, text in string_leaves(raws[name]):
            for other in others:
                if f"{other}." in text or f"DOC-{PROJECT_PREFIX[other]}-" in text:
                    report.error(
                        LEDGER_FILES[name], path, f"I3: references the other project ({text!r})"
                    )
                    break


def check_names(
    raws: dict[str, dict[str, Any]], company: ls.CompanyLedger | None, report: Report
) -> None:
    if company is None:
        return
    whitelist = set(company.name_whitelist)
    for spec_name in ls.SPEC_FICTIONAL_NAMES:
        if spec_name not in whitelist:
            report.error(
                "company.yaml", "name_whitelist", f"N3: missing SPEC_05 §4 name {spec_name!r}"
            )
    for i, party in enumerate(company.parties):
        if str(party.name.value) not in whitelist:
            report.error("company.yaml", f"parties[{i}].name.value", "N2: not in name_whitelist")
    institutions = set(company.public_institutions)
    for name, raw in raws.items():
        for path, text in string_leaves(raw):
            if path == "name_whitelist" or path.startswith("name_whitelist["):
                continue
            for match in _NAME_PATTERN.findall(text):
                if match in whitelist or match in institutions:
                    continue
                if any(match.endswith(w) or w.endswith(match) for w in whitelist):
                    continue
                report.error(
                    LEDGER_FILES[name], path, f"N1: company-like name {match!r} not whitelisted"
                )


def check_documents(
    raws: dict[str, dict[str, Any]],
    ledgers: dict[str, LedgerModel],
    report: Report,
) -> None:
    all_ids: dict[str, str] = {}
    for name, ledger in ledgers.items():
        for i, doc in enumerate(ledger.documents):
            if doc.id in all_ids:
                report.error(LEDGER_FILES[name], f"documents[{i}].id", f"D2: duplicate id {doc.id}")
            all_ids[doc.id] = name
            if doc.id.split("-")[1] != PROJECT_PREFIX[name]:
                report.error(
                    LEDGER_FILES[name],
                    f"documents[{i}].id",
                    f"D2: prefix must be {PROJECT_PREFIX[name]}",
                )
            if doc.name.value == "" or not isinstance(doc.name.value, str):
                report.error(
                    LEDGER_FILES[name],
                    f"documents[{i}].name.value",
                    "D2: name must be a non-empty string",
                )

    for name, ledger in ledgers.items():
        file = LEDGER_FILES[name]
        ids_here = {doc.id for doc in ledger.documents}
        for i, doc in enumerate(ledger.documents):
            for field_name in ("supersedes", "superseded_by"):
                ref = getattr(doc, field_name)
                if ref is not None and ref not in ids_here:
                    report.error(
                        file, f"documents[{i}].{field_name}", f"D2: unknown document {ref}"
                    )
            for j, ref in enumerate(doc.related):
                if ref not in all_ids:
                    report.error(
                        file, f"documents[{i}].related[{j}]", f"D2: unknown document {ref}"
                    )
            for key, path in doc.key_facts.items():
                try:
                    resolve_path(raws[name], path)
                except (KeyError, IndexError, TypeError):
                    report.error(
                        file,
                        f"documents[{i}].key_facts.{key}",
                        f"F8: ledger path {path!r} not found",
                    )
        # every DOC-... reference anywhere in the file must resolve
        for path, text in string_leaves(raws[name]):
            if (
                re.fullmatch(r"DOC-(ANK|IZM|CO|YSV|BOZ|GNS|AKY|DMR)-[A-Z]{3}-\d{3}", text)
                and text not in all_ids
            ):
                report.error(file, path, f"D2: unknown document {text}")


def check_version_links(ledgers: dict[str, LedgerModel], report: Report) -> None:
    """Phase 5.1 (SPEC_05 §11 "Legal"/"Version"): generalizes F6's Facility-chain-only
    rule to every document. Two parts: (1) `supersedes`/`superseded_by` must be mutual
    wherever either is set — a one-way link is almost always a copy-paste mistake in a
    52-document inventory; (2) for every maximal chain built by following that mutual
    link, exactly the last (most recent) document may be non-`superseded`. Documents
    that never set `supersedes`/`superseded_by` (e.g. a licence and its amendment, linked
    only via `related` — a different relationship: the amendment overlays, it doesn't
    replace) are outside this rule entirely."""
    by_id: dict[str, tuple[str, ls.Document]] = {
        doc.id: (LEDGER_FILES[name], doc)
        for name, ledger in ledgers.items()
        for doc in ledger.documents
    }
    for doc_id, (file, doc) in by_id.items():
        if doc.supersedes is not None and doc.supersedes in by_id:
            pred = by_id[doc.supersedes][1]
            if pred.superseded_by != doc_id:
                report.error(
                    file,
                    f"documents[{doc_id}].supersedes",
                    f"V1: {doc_id} supersedes {doc.supersedes}, but its superseded_by is "
                    f"{pred.superseded_by!r}, not {doc_id!r}",
                )
        if doc.superseded_by is not None and doc.superseded_by in by_id:
            succ = by_id[doc.superseded_by][1]
            if succ.supersedes != doc_id:
                report.error(
                    file,
                    f"documents[{doc_id}].superseded_by",
                    f"V1: {doc_id} is superseded by {doc.superseded_by}, but its supersedes is "
                    f"{succ.supersedes!r}, not {doc_id!r}",
                )

    visited: set[str] = set()
    for start_id in by_id:
        if start_id in visited:
            continue
        # walk to the chain's root (oldest link with no predecessor still in the ledger)
        root, seen = start_id, {start_id}
        while by_id[root][1].supersedes in by_id and by_id[root][1].supersedes not in seen:
            root = by_id[root][1].supersedes  # type: ignore[assignment]
            seen.add(root)
        # walk forward from the root to collect the full chain
        chain, cur = [root], root
        while by_id[cur][1].superseded_by in by_id and by_id[cur][1].superseded_by not in visited:
            nxt = by_id[cur][1].superseded_by
            assert nxt is not None
            if nxt in chain:
                break
            chain.append(nxt)
            cur = nxt
        visited.update(chain)
        if len(chain) < 2:
            continue
        # Same "current" definition as F6: a chain link is draft/superseded/whatever in
        # between, but exactly the last one is executed/active (mirrors F6's own check —
        # a link that was superseded before ever taking effect, like FIN-001's DRAFT, is
        # not literally "superseded" and must not be mistaken for current either).
        current = [d for d in chain if by_id[d][1].status in ("executed", "active")]
        if current != [chain[-1]]:
            report.error(
                "*",
                f"documents chain {chain[0]}..{chain[-1]}",
                f"V2: exactly the last link must be executed/active, got {current}",
            )


def check_technical(ankara: ls.AnkaraLedger, report: Report) -> None:
    """SPEC_05 §11 "Technical": a coarse sanity check — declared turbine count times the
    ledger's own "5 MW sınıfı" description should land near the declared current
    capacity. A soft WARNING (the class description is free text, not a machine fact) that
    catches the obvious slip of changing one without the other."""
    f = "ankara_res.yaml"
    turbines = ankara.project.turbines
    implied = float(turbines.count.value) * 5.0  # type: ignore[arg-type]
    current = float(ankara.project.capacity_mw.current.value)  # type: ignore[arg-type]
    if abs(implied - current) > 5.0:
        report.warning(
            f,
            "project.turbines.count.value",
            f"T1: {turbines.count.value} türbin × ~5 MW ≈ {implied:.0f} MW, "
            f"declared capacity_mw.current is {current:.0f} MW",
        )


_DISTRIBUTION_CAP = 80
_DISTRIBUTION_TARGETS = {"ankara_res": 45, "izmir_res": 15, "company": 10}
_SCANNED_RANGE = (8, 10)
_DISTRIBUTION_TOLERANCE = 0.3
_GENERATED_PHASES = ("3.1", "5.1")


def check_document_distribution(ledgers: dict[str, LedgerModel], report: Report) -> None:
    """SPEC_05 §6: ~70 documents (Ankara ~45, İzmir ~15, company ~10), hard cap 80,
    8-10 of them scanned. Replaces the old G1 hardcoded-15 warning (Phase 3.1 -> 5.1:
    the count is no longer a single fixed number, so only the cap is a hard ERROR — the
    per-bucket/scanned targets are SPEC's own "yaklaşık", kept as WARNING with generous
    (±30%) tolerance)."""
    generated = {
        name: [d for d in ledger.documents if d.generate_in_phase in _GENERATED_PHASES]
        for name, ledger in ledgers.items()
    }
    total = sum(len(docs) for docs in generated.values())
    if total > _DISTRIBUTION_CAP:
        report.error(
            "*", "documents", f"G1: {total} documents, cap is {_DISTRIBUTION_CAP} (SPEC_05 §6)"
        )
    for name, target in _DISTRIBUTION_TARGETS.items():
        n = len(generated.get(name, []))
        if abs(n - target) > target * _DISTRIBUTION_TOLERANCE:
            report.warning(
                LEDGER_FILES[name], "documents", f"G1: {n} documents, SPEC_05 §6 target ~{target}"
            )
    scanned = sum(1 for docs in generated.values() for d in docs if d.source_type == "scanned_pdf")
    lo, hi = _SCANNED_RANGE
    if not lo <= scanned <= hi:
        report.warning(
            "*", "documents", f"G1: {scanned} scanned_pdf documents, SPEC_05 §6 target {lo}-{hi}"
        )


def check_meta(models: dict[str, BaseModel | None], report: Report) -> None:
    todays: dict[str, date] = {}
    for name, model in models.items():
        if model is not None:
            todays[name] = model.meta.demo_today  # every ledger model has `meta`
    if len(set(todays.values())) > 1:
        report.error("*", "meta.demo_today", f"C10: files disagree {todays}")
    env = os.environ.get("DEMO_TODAY")
    if env and todays:
        try:
            env_date = date.fromisoformat(env)
        except ValueError:
            report.warning("*", "meta.demo_today", f"C10: DEMO_TODAY env {env!r} is not ISO")
        else:
            for name, value in todays.items():
                if value != env_date:
                    report.error(
                        LEDGER_FILES.get(name, name),
                        "meta.demo_today",
                        f"C10: {value} != DEMO_TODAY {env_date}",
                    )


def check_fx(fx: ls.FxLedger, report: Report) -> None:
    f = "fx_rates.yaml"
    seen: dict[tuple[str, str], float] = {}
    for i, rate in enumerate(fx.rates):
        key = (rate.pair, rate.period)
        if key in seen:
            report.error(f, f"rates[{i}]", f"duplicate {rate.pair} {rate.period}")
        seen[key] = rate.rate
    for (pair, period), value in seen.items():
        if pair != "EUR/USD":
            continue
        eur_try, usd_try = seen.get(("EUR/TRY", period)), seen.get(("USD/TRY", period))
        if eur_try and usd_try:
            implied = eur_try / usd_try
            if abs(implied - value) / value > FX_CROSS_TOLERANCE:
                report.error(f, f"rates EUR/USD {period}", f"cross rate {implied:.4f} vs {value}")


def check_questions(
    qs: ls.QuestionSet,
    raws: dict[str, dict[str, Any]],
    ledgers: dict[str, LedgerModel],
    report: Report,
) -> None:
    f = "questions.json"
    ids: set[str] = set()
    doc_names: set[str] = set()
    doc_types: set[str] = set()
    for ledger in ledgers.values():
        for doc in ledger.documents:
            doc_names.add(str(doc.name.value))
            doc_types.add(doc.type)
    project_names = set(QUOTAS)
    project_counts = dict.fromkeys(QUOTAS, 0)
    category_counts: dict[str, int] = {}
    for i, q in enumerate(qs.questions):
        p = f"questions[{i}]"
        if q.id in ids:
            report.error(f, f"{p}.id", f"Q5: duplicate id {q.id}")
        ids.add(q.id)
        if q.expected_project in project_counts:
            project_counts[q.expected_project] += 1  # type: ignore[index]
        category_counts[q.category] = category_counts.get(q.category, 0) + 1
        if q.category == "hallucination" and not q.expect_no_answer:
            report.error(f, f"{p}.expect_no_answer", "Q3: hallucination questions expect no answer")
        if q.category == "authorization" and (q.ask_as_user != "enerji" or not q.expect_no_answer):
            report.error(
                f, f"{p}", "Q3: authorization questions are asked as enerji and expect no answer"
            )
        refs = q.expected_answer if isinstance(q.expected_answer, list) else [q.expected_answer]
        for ref_raw in refs:
            if ref_raw is None or not ref_raw.startswith("ledger:"):
                continue
            ref = ref_raw[len("ledger:") :]
            file_key, _, path = ref.partition(".")
            if file_key not in raws:
                report.error(f, f"{p}.expected_answer", f"Q4: unknown ledger file {file_key!r}")
            else:
                try:
                    resolve_path(raws[file_key], path)
                except (KeyError, IndexError, TypeError):
                    report.error(f, f"{p}.expected_answer", f"Q4: ledger path {path!r} not found")
        if q.category == "comparison":
            # Ü-3: two projects, two ledger facts, a forbidden-wording list, no single project.
            if not isinstance(q.expected_answer, list) or len(q.expected_answer) < 2:
                report.error(
                    f, f"{p}.expected_answer", "Q6: comparison needs a list of >= 2 ledger facts"
                )
            if q.expected_project is not None:
                report.error(f, f"{p}.expected_project", "Q6: comparison spans projects, use null")
            if not q.forbidden_phrases:
                report.error(f, f"{p}.forbidden_phrases", "Q6: comparison needs forbidden_phrases")
        if q.category == "discovery":
            # Q8: a discovery question has no single expected value; it needs the documents
            # Balbal should surface, and never declares a no-answer or an assist kind.
            if not q.required_sources:
                report.error(f, f"{p}.required_sources", "Q8: discovery needs required_sources")
            if q.expect_no_answer or q.expect_assist is not None:
                report.error(f, f"{p}", "Q8: discovery is scored by discovery_check, not no-answer")
        elif not q.expect_no_answer and q.expected_answer is None:
            report.error(
                f, f"{p}.expected_answer", "Q4: answerable question needs an expected_answer"
            )
        # Q7 (ADR-027): assist categories are no-answer questions with a declared assist kind;
        # `expect_assist` never rides on a question that expects an answer.
        if q.category in ("ambiguous", "term_mismatch"):
            if not q.expect_no_answer or q.expected_answer is not None:
                report.error(f, f"{p}", f"Q7: {q.category} questions expect no answer")
            if q.expect_assist is None:
                report.error(f, f"{p}.expect_assist", f"Q7: {q.category} needs expect_assist")
        if q.expect_assist is not None and not q.expect_no_answer:
            report.error(f, f"{p}.expect_assist", "Q7: expect_assist requires expect_no_answer")
        for j, source in enumerate(q.required_sources):
            if source not in doc_names and source not in doc_types:
                report.error(
                    f, f"{p}.required_sources[{j}]", f"Q4: {source!r} is not a document name/type"
                )
        for j, source in enumerate(q.forbidden_sources):
            if source not in doc_names and source not in doc_types and source not in project_names:
                report.error(
                    f, f"{p}.forbidden_sources[{j}]", f"Q4: {source!r} is not a document or project"
                )
    if len(qs.questions) < MIN_QUESTIONS:
        report.error(f, "questions", f"Q2: {len(qs.questions)} questions, need >= {MIN_QUESTIONS}")
    for project, minimum in QUOTAS.items():
        if project_counts[project] < minimum:
            report.error(
                f,
                "questions",
                f"Q2: {project} has {project_counts[project]} questions, need >= {minimum}",
            )
    for category, minimum in CATEGORY_QUOTAS.items():
        if category_counts.get(category, 0) < minimum:
            report.error(
                f,
                "questions",
                f"Q2: {category} has {category_counts.get(category, 0)}, need >= {minimum}",
            )


# ---------------------------------------------------------------- entrypoint


def validate(master: Path, questions: Path | None) -> tuple[Report, dict[str, int]]:
    report = Report()
    raws: dict[str, dict[str, Any]] = {}
    for name, filename in LEDGER_FILES.items():
        path = master / filename
        if not path.exists():
            report.error(filename, "<file>", "missing")
            continue
        try:
            raws[name] = load_yaml(path)
        except yaml.YAMLError as exc:
            report.error(filename, "<file>", f"YAML parse error: {exc}")

    models: dict[str, BaseModel | None] = {}
    if "company" in raws:
        models["company"] = parse_model(ls.CompanyLedger, raws["company"], "company.yaml", report)
    if "ankara_res" in raws:
        models["ankara_res"] = parse_model(
            ls.AnkaraLedger, raws["ankara_res"], "ankara_res.yaml", report
        )
    if "izmir_res" in raws:
        models["izmir_res"] = parse_model(
            ls.IzmirLedger, raws["izmir_res"], "izmir_res.yaml", report
        )
    if "fx_rates" in raws:
        models["fx_rates"] = parse_model(ls.FxLedger, raws["fx_rates"], "fx_rates.yaml", report)
    # Adım 5 Aşama C (10.10.2026): any ledger file beyond the original 4 is one of the new
    # SPVs (ADIM5_ASAMA_C_PLAN.md §2.2) — dispatched to its shape by `project.stage`, not a
    # hardcoded per-project branch. No file uses this yet; it activates as Aşama C.3 adds
    # `yesilova_res.yaml` etc. and their `LEDGER_FILES`/`PROJECT_PREFIX` entries.
    _core_files = {"company", "ankara_res", "izmir_res", "fx_rates"}
    for name in raws:
        if name in _core_files:
            continue
        filename = LEDGER_FILES.get(name, name)
        stage = (raws[name].get("project") or {}).get("stage")
        if stage == "operation":
            models[name] = parse_model(ls.OperatingLedger, raws[name], filename, report)
        elif stage == "development":
            models[name] = parse_model(ls.GenericDevelopmentLedger, raws[name], filename, report)
        else:
            report.error(filename, "project.stage", f"unknown stage {stage!r} for a generic SPV")

    check_meta(models, report)
    company = models.get("company")
    ankara = models.get("ankara_res")
    izmir = models.get("izmir_res")
    fx = models.get("fx_rates")
    if isinstance(ankara, ls.AnkaraLedger):
        check_chronology(ankara, report)
        check_finance(ankara, report)
        check_document_dates("ankara_res.yaml", ankara.documents, ankara.meta.demo_today, report)
    if "izmir_res" in raws:
        check_izmir_isolation(
            raws["izmir_res"], izmir if isinstance(izmir, ls.IzmirLedger) else None, report
        )
    if isinstance(izmir, ls.IzmirLedger):
        check_izmir_timeline(izmir, report)
        check_document_dates("izmir_res.yaml", izmir.documents, izmir.meta.demo_today, report)
    if isinstance(company, ls.CompanyLedger):
        check_document_dates("company.yaml", company.documents, company.meta.demo_today, report)
    for name, model in models.items():
        if isinstance(model, ls.OperatingLedger | ls.GenericDevelopmentLedger):
            check_document_dates(
                LEDGER_FILES.get(name, name), model.documents, model.meta.demo_today, report
            )
    check_cross_project_refs(raws, report)
    check_names(raws, company if isinstance(company, ls.CompanyLedger) else None, report)
    check_conflict_groups(raws, report)
    ledgers = {name: model for name, model in models.items() if isinstance(model, LedgerModel)}
    if ledgers:
        check_documents(raws, ledgers, report)
        check_version_links(ledgers, report)
        check_document_distribution(ledgers, report)
    if isinstance(ankara, ls.AnkaraLedger):
        check_technical(ankara, report)
    if isinstance(fx, ls.FxLedger):
        check_fx(fx, report)

    if questions is not None:
        if not questions.exists():
            report.error("questions.json", "<file>", "missing")
        else:
            with questions.open(encoding="utf-8") as handle:
                raw_questions = json.load(handle)
            qs = parse_model(ls.QuestionSet, raw_questions, "questions.json", report)
            if qs is not None and ledgers:
                check_questions(qs, raws, ledgers, report)

    tags = {"USER_FACT": 0, "AI_ASSUMPTION": 0}
    for raw in raws.values():
        for key, n in count_tags(raw).items():
            tags[key] += n
    return report, tags


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_ledger")
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--no-questions", action="store_true")
    parser.add_argument(
        "--summary", action="store_true", help="print USER_FACT / AI_ASSUMPTION counts"
    )
    args = parser.parse_args(argv)

    report, tags = validate(args.master, None if args.no_questions else args.questions)
    for issue in report.issues:
        print(issue.render())
    if args.summary:
        print(f"tags: USER_FACT={tags['USER_FACT']} AI_ASSUMPTION={tags['AI_ASSUMPTION']}")
    print(f"{report.error_count} error(s), {report.warning_count} warning(s)")
    return 0 if report.error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
