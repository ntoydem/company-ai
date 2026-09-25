"""Phase 4.1 eval runner — pure logic (no network): loading `questions.json`, resolving
each question's expected ledger value into checkable text, matching required/forbidden
sources against a document catalog, scoring one question, and aggregating a report.

`scripts/run_eval.py` is the thin CLI/HTTP layer that drives this module; splitting the
two keeps everything here testable without a running backend (`backend/tests/test_eval_lib.py`).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from seed_data.generator import facts as facts_mod
from seed_data.generator import ledger_schema as ls
from seed_data.generator.validate_ledger import DEFAULT_MASTER, DEFAULT_QUESTIONS, resolve_path

DEFAULT_MANIFEST = DEFAULT_MASTER.parent / "documents" / "manifest.json"
DEFAULT_EXCEL_MANIFEST = DEFAULT_MASTER.parent / "excel" / "manifest.json"
DEFAULT_RESULTS_DIR = DEFAULT_MASTER.parent / "evaluation" / "results"

# Categories PHASES.md requires 100% on; every other category needs >= 80%.
HUNDRED_PERCENT_CATEGORIES = frozenset({"isolation", "hallucination", "authorization"})
DEFAULT_THRESHOLD_PCT = 80.0

_PROJECT_NAME_BY_CODE = {"ANK_RES": "Ankara RES", "IZM_RES": "İzmir RES"}

# Enum-like strings that never get formatted into a document as a `[[token]]` (unlike
# `ced_status`, which is a real `_FIELD_KIND` entry) — hand-verified against the actual
# generated PDFs once; extend only after checking the rendered text, never by guessing.
_STRING_ALIASES: dict[str, tuple[str, ...]] = {}


# ---------------------------------------------------------------- loading


def load_questions(path: Path = DEFAULT_QUESTIONS) -> ls.QuestionSet:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ls.QuestionSet.model_validate(raw)


def load_ledger_raws(master_dir: Path = DEFAULT_MASTER) -> dict[str, Any]:
    return facts_mod.load_raws(master_dir)


# ---------------------------------------------------------------- document catalog


@dataclass(frozen=True)
class DocumentCatalog:
    """`seed_data/documents/manifest.json` + `seed_data/excel/manifest.json`, indexed for
    required/forbidden source checks — read once, locally; no API round trip (Phase 4.1
    plan T5). Workbooks (Phase 4.3) are cited by file name in `excel_sources`, so
    `file_to_title` maps them back to the ledger title the golden set names."""

    title_to_type: dict[str, str]
    title_to_project: dict[str, str]
    file_to_title: dict[str, str] = field(default_factory=dict)

    @property
    def titles(self) -> frozenset[str]:
        return frozenset(self.title_to_type)

    @property
    def types(self) -> frozenset[str]:
        return frozenset(self.title_to_type.values())

    @property
    def project_names(self) -> frozenset[str]:
        return frozenset(_PROJECT_NAME_BY_CODE.values())

    def cited_titles(self, titles: tuple[str, ...], files: tuple[str, ...]) -> frozenset[str]:
        """Document titles cited directly plus the titles of cited workbook files."""
        return frozenset(titles) | frozenset(
            self.file_to_title[f] for f in files if f in self.file_to_title
        )


def build_document_catalog(
    manifest_path: Path = DEFAULT_MANIFEST, excel_manifest_path: Path = DEFAULT_EXCEL_MANIFEST
) -> DocumentCatalog:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = list(manifest["documents"])
    if excel_manifest_path.exists():
        entries += json.loads(excel_manifest_path.read_text(encoding="utf-8"))["workbooks"]
    title_to_type: dict[str, str] = {}
    title_to_project: dict[str, str] = {}
    file_to_title: dict[str, str] = {}
    for entry in entries:
        title = entry["title"]
        title_to_type[title] = entry["document_type"]
        project_code = entry.get("project_code")
        if project_code in _PROJECT_NAME_BY_CODE:
            title_to_project[title] = _PROJECT_NAME_BY_CODE[project_code]
        if entry.get("source_type") == "xlsx":
            file_to_title[entry["file"]] = title
    return DocumentCatalog(
        title_to_type=title_to_type, title_to_project=title_to_project, file_to_title=file_to_title
    )


def _source_satisfied(name: str, cited_titles: frozenset[str], catalog: DocumentCatalog) -> bool:
    """`name` (a `required_sources`/`forbidden_sources` entry) is a document title, a
    document type, or (forbidden-only) a project name — same three-way rule
    `validate_ledger.py::check_questions` uses to validate `questions.json` itself."""
    if name in catalog.titles and name in cited_titles:
        return True
    # "Facility Agreement" is both one document's title and the type shared by its draft
    # and amendments; the golden set uses the bare name in both senses, so either reading
    # satisfies it (same "name or type" rule `validate_ledger.py` applies to the set).
    if name in catalog.types:
        return any(catalog.title_to_type.get(t) == name for t in cited_titles)
    if name in catalog.titles:
        return False
    if name in catalog.project_names:
        return any(catalog.title_to_project.get(t) == name for t in cited_titles)
    return False


# ---------------------------------------------------------------- expected value


@dataclass(frozen=True)
class ExpectedValue:
    """`required`: one tuple of acceptable spellings per independent fact the answer must
    contain (usually one; two for a "what was it, what is it now" compound question like
    `ANK-FIN-013`). Value-check passes iff every group has >= 1 spelling present in the
    answer text. `skip=True` means the resolved ledger value has no reliable literal
    text form (a list, an unmapped enum string, a "hasn't happened yet" `None`, or a
    `DOC-*` document reference already covered by `required_sources`) — the question is
    then scored on sources + `answered` alone (Phase 4.1 plan SORU 1, approved)."""

    required: tuple[tuple[str, ...], ...] = ()
    skip: bool = False
    skip_reason: str | None = None


def _classify_and_format(value: Any, path: str, parent: Any) -> tuple[str, ...] | None:
    """Acceptable spellings for one scalar ledger value, or `None` if it can't be
    reliably formatted (caller decides what that means)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, date):
        # TR (what the prompt asks for), ISO, and the EN long form English documents print.
        return (
            facts_mod.format_date(value, "tr"),
            value.isoformat(),
            facts_mod.format_date(value, "en"),
        )
    if isinstance(value, str) and value.startswith("DOC-"):
        return None  # a document reference, not literal text — see required_sources
    if isinstance(value, str) and value in _STRING_ALIASES:
        return _STRING_ALIASES[value]
    if isinstance(value, str) and path.endswith(".name"):
        return (value,)  # identity key (e.g. `project.name: Ankara RES`) — literal
    if isinstance(value, int | float | str):
        formatted = facts_mod.format_ledger_leaf(path, value, parent, "tr")
        if formatted is None:
            return None
        alts = [formatted]
        if "," in formatted:
            alts.append(formatted.replace(",", "."))  # EN-decimal alias
        money_alias = _money_en_grouping_alias(formatted, value)
        if money_alias is not None:
            alts.append(money_alias)
        mwh_alias = _mwh_grouped_alias(formatted, value)
        if mwh_alias is not None:
            alts.append(mwh_alias)
        return tuple(alts)
    return None  # list / dict / None


def resolve_expected(question: ls.Question, raws: dict[str, Any]) -> ExpectedValue:
    ea = question.expected_answer
    if ea is None:
        return ExpectedValue(skip=True, skip_reason="expect_no_answer")
    ref = ea.removeprefix("ledger:")
    file_key, _, path = ref.partition(".")
    value = resolve_path(raws[file_key], path)
    parent_path = path.rsplit(".", 1)[0] if "." in path else None
    parent = resolve_path(raws[file_key], parent_path) if parent_path else None

    scalar = _classify_and_format(value, path, parent)
    if scalar is not None:
        return ExpectedValue(required=(scalar,))

    if (
        isinstance(value, dict)
        and {"initial", "current"} <= set(value)
        and all(isinstance(value[k], dict) and "value" in value[k] for k in ("initial", "current"))
    ):
        groups: list[tuple[str, ...]] = []
        for key in ("initial", "current"):
            sub = _classify_and_format(value[key]["value"], f"{path}.{key}.value", value[key])
            if sub is None:
                return ExpectedValue(skip=True, skip_reason=f"unformattable compound leaf: {key}")
            groups.append(sub)
        return ExpectedValue(required=tuple(groups))

    return ExpectedValue(
        skip=True, skip_reason=f"unformattable expected_answer type: {type(value).__name__}"
    )


_TR_MONEY = re.compile(r"^([\d.]+) (EUR|USD|TRY)$")


def _money_en_grouping_alias(formatted: str, value: Any) -> str | None:
    """`format_ledger_leaf` always groups thousands the TR way (`50.400.000 EUR`), but
    the source documents themselves are half English (finance) and the model sometimes
    relays the money figure exactly as printed there (`50,400,000 EUR`) instead of
    reformatting it — observed live in the Phase 4.1 eval run (`ANK-FIN-011`). Accept
    both rather than treating that as a wrong answer."""
    match = _TR_MONEY.match(formatted)
    if match is None or not isinstance(value, int | float):
        return None
    return f"{round(value):,} {match.group(2)}"


_UNGROUPED_MWH = re.compile(r"^\d{4,} MWh$")


def _mwh_grouped_alias(formatted: str, value: Any) -> str | None:
    """The generated documents print MWh ungrouped (`13538 MWh`, `format_value("mwh")`),
    the Excel engine's Turkish formatting groups thousands (`13.538 MWh`, Phase 4.2
    `format_value`). A DATA answer relays the engine's form — accept both."""
    if _UNGROUPED_MWH.match(formatted) is None or not isinstance(value, int | float):
        return None
    return f"{round(value):,}".replace(",", ".") + " MWh"


_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip().lower()


def value_check_passes(expected: ExpectedValue, answer_text: str) -> bool:
    haystack = _normalize(answer_text)
    return all(
        any(_normalize(spelling) in haystack for spelling in group) for group in expected.required
    )


# ---------------------------------------------------------------- scoring


@dataclass(frozen=True)
class AskOutcome:
    """What `run_eval.py` got back for one question — either a real `/api/ask` response
    or a network/LLM failure after retries were exhausted (`error` set, everything else
    default)."""

    answered: bool = False
    answer_text: str = ""
    cited_titles: tuple[str, ...] = ()
    cited_files: tuple[str, ...] = ()  # `excel_sources[].file` (Phase 4.3)
    query_type: str | None = None
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    error: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class QuestionResult:
    id: str
    category: str
    ask_as_user: str
    question: str
    expect_no_answer: bool
    answered: bool
    answer_text: str
    cited_titles: tuple[str, ...]
    answered_ok: bool
    required_sources_missing: tuple[str, ...]
    forbidden_sources_hit: tuple[str, ...]
    value_check: str  # "pass" | "fail" | "skipped"
    value_check_reason: str | None
    passed: bool
    error: str | None
    latency_ms: int
    tokens_in: int
    tokens_out: int
    model: str | None
    query_type: str | None = None  # router decision (Phase 4.3), informational


def score_question(
    question: ls.Question, expected: ExpectedValue, catalog: DocumentCatalog, outcome: AskOutcome
) -> QuestionResult:
    if outcome.error is not None:
        return QuestionResult(
            id=question.id,
            category=question.category,
            ask_as_user=question.ask_as_user,
            question=question.question,
            expect_no_answer=question.expect_no_answer,
            answered=False,
            answer_text="",
            cited_titles=(),
            answered_ok=False,
            required_sources_missing=(),
            forbidden_sources_hit=(),
            value_check="skipped",
            value_check_reason="not evaluated: request error",
            passed=False,
            error=outcome.error,
            latency_ms=outcome.latency_ms,
            tokens_in=0,
            tokens_out=0,
            model=None,
        )

    cited = catalog.cited_titles(outcome.cited_titles, outcome.cited_files)
    answered_ok = outcome.answered == (not question.expect_no_answer)

    missing_required = ()
    if not question.expect_no_answer:
        missing_required = tuple(
            name
            for name in question.required_sources
            if not _source_satisfied(name, cited, catalog)
        )
    forbidden_hit = tuple(
        name for name in question.forbidden_sources if _source_satisfied(name, cited, catalog)
    )
    sources_ok = not missing_required and not forbidden_hit

    if expected.skip:
        value_check = "skipped"
        value_check_reason = expected.skip_reason
    elif value_check_passes(expected, outcome.answer_text):
        value_check = "pass"
        value_check_reason = None
    else:
        value_check = "fail"
        value_check_reason = "expected value text not found in answer"

    passed = answered_ok and sources_ok and value_check != "fail"

    return QuestionResult(
        id=question.id,
        category=question.category,
        ask_as_user=question.ask_as_user,
        question=question.question,
        expect_no_answer=question.expect_no_answer,
        answered=outcome.answered,
        answer_text=outcome.answer_text,
        cited_titles=tuple(sorted(cited)),
        answered_ok=answered_ok,
        required_sources_missing=missing_required,
        forbidden_sources_hit=forbidden_hit,
        value_check=value_check,
        value_check_reason=value_check_reason,
        passed=passed,
        error=None,
        latency_ms=outcome.latency_ms,
        tokens_in=outcome.tokens_in,
        tokens_out=outcome.tokens_out,
        model=outcome.model,
        query_type=outcome.query_type,
    )


# ---------------------------------------------------------------- report


@dataclass(frozen=True)
class CategoryScore:
    category: str
    total: int
    evaluated: int
    passed: int
    errored: int
    threshold_pct: float

    @property
    def pct(self) -> float:
        return 100.0 * self.passed / self.evaluated if self.evaluated else 0.0

    @property
    def meets_threshold(self) -> bool:
        return self.evaluated > 0 and self.pct >= self.threshold_pct


@dataclass(frozen=True)
class EvalReport:
    model: str | None
    date: str
    demo_today: str
    embeddings_enabled: bool
    partial: bool
    partial_reason: str | None
    results: tuple[QuestionResult, ...]
    categories: tuple[CategoryScore, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return bool(self.categories) and all(c.meets_threshold for c in self.categories)

    @property
    def skipped_value_checks(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.error is None and r.value_check == "skipped")

    @property
    def errored(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.error is not None)


def build_report(
    results: list[QuestionResult],
    *,
    model: str | None,
    date_str: str,
    demo_today: str,
    embeddings_enabled: bool,
    partial: bool = False,
    partial_reason: str | None = None,
) -> EvalReport:
    by_category: dict[str, list[QuestionResult]] = {}
    for result in results:
        by_category.setdefault(result.category, []).append(result)

    categories = []
    for category, rows in sorted(by_category.items()):
        evaluated_rows = [r for r in rows if r.error is None]
        threshold = 100.0 if category in HUNDRED_PERCENT_CATEGORIES else DEFAULT_THRESHOLD_PCT
        categories.append(
            CategoryScore(
                category=category,
                total=len(rows),
                evaluated=len(evaluated_rows),
                passed=sum(1 for r in evaluated_rows if r.passed),
                errored=sum(1 for r in rows if r.error is not None),
                threshold_pct=threshold,
            )
        )

    return EvalReport(
        model=model,
        date=date_str,
        demo_today=demo_today,
        embeddings_enabled=embeddings_enabled,
        partial=partial,
        partial_reason=partial_reason,
        results=tuple(results),
        categories=tuple(categories),
    )


def report_to_json(report: EvalReport) -> dict[str, Any]:
    return {
        "model": report.model,
        "date": report.date,
        "demo_today": report.demo_today,
        "embeddings_enabled": report.embeddings_enabled,
        "partial": report.partial,
        "partial_reason": report.partial_reason,
        "ok": report.ok,
        "categories": [
            {
                "category": c.category,
                "total": c.total,
                "evaluated": c.evaluated,
                "passed": c.passed,
                "errored": c.errored,
                "pct": round(c.pct, 1),
                "threshold_pct": c.threshold_pct,
                "meets_threshold": c.meets_threshold,
            }
            for c in report.categories
        ],
        "questions": [
            {
                "id": r.id,
                "category": r.category,
                "ask_as_user": r.ask_as_user,
                "question": r.question,
                "expect_no_answer": r.expect_no_answer,
                "answered": r.answered,
                "answer_text": r.answer_text,
                "cited_titles": list(r.cited_titles),
                "query_type": r.query_type,
                "answered_ok": r.answered_ok,
                "required_sources_missing": list(r.required_sources_missing),
                "forbidden_sources_hit": list(r.forbidden_sources_hit),
                "value_check": r.value_check,
                "value_check_reason": r.value_check_reason,
                "passed": r.passed,
                "error": r.error,
                "latency_ms": r.latency_ms,
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "model": r.model,
            }
            for r in report.results
        ],
    }


def render_markdown(report: EvalReport) -> str:
    lines = [
        f"# Eval sonucu — {report.model or '(model bilinmiyor)'} — {report.date}",
        "",
        f"`DEMO_TODAY`: {report.demo_today} · `EMBEDDINGS_ENABLED`: {report.embeddings_enabled}",
    ]
    if report.partial:
        lines.append(f"\n**Koşu yarıda kesildi:** {report.partial_reason}")
    lines += [
        "",
        "## Kategori bazlı sonuç",
        "",
        "| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |",
        "|---|---|---|---|---|",
    ]
    for c in report.categories:
        mark = "✅" if c.meets_threshold else "❌"
        passed_frac = f"{c.passed}/{c.evaluated}"
        lines.append(
            f"| {c.category} | ≥%{c.threshold_pct:g} | {mark} %{c.pct:.1f} | {passed_frac} "
            f"(toplam {c.total}) | {c.errored} |"
        )
    lines.append("")
    verdict = "✅ tüm eşikler karşılandı" if report.ok else "❌ en az bir kategori eşiği altında"
    lines.append(f"**Genel sonuç:** {verdict}")

    failed = [r for r in report.results if r.error is None and not r.passed]
    if failed:
        lines += ["", "## Başarısız sorular", ""]
        for r in failed:
            reasons = []
            if not r.answered_ok:
                reasons.append(f"answered={r.answered} bekleniyordu={not r.expect_no_answer}")
            if r.required_sources_missing:
                reasons.append(f"eksik kaynak: {list(r.required_sources_missing)}")
            if r.forbidden_sources_hit:
                reasons.append(f"yasak kaynak geldi: {list(r.forbidden_sources_hit)}")
            if r.value_check == "fail":
                reasons.append("beklenen değer metinde bulunamadı")
            snippet = r.answer_text[:200].replace("\n", " ")
            lines.append(f"- **{r.id}** ({r.category}): {'; '.join(reasons)} — cevap: “{snippet}”")

    errored = report.errored
    if errored:
        lines += ["", "## Puanlanamayan sorular (istek hatası)", ""]
        for r in errored:
            lines.append(f"- **{r.id}** ({r.category}): {r.error}")

    skipped = report.skipped_value_checks
    if skipped:
        lines += [
            "",
            "## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)",
            "",
            "Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin "
            "olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.",
            "",
        ]
        for r in skipped:
            lines.append(f"- **{r.id}** ({r.category}): {r.value_check_reason}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- target pages (Phase 3.2b)

Page = tuple[str, int]  # (document title, page number)


@dataclass(frozen=True)
class TargetIndex:
    """Ledger path -> the (title, page) pairs where that fact is physically printed.

    Derived without an LLM: each ledger `documents[].key_facts` entry names a ledger path,
    `manifest.json`'s `key_facts_used` holds the literal text substituted for it, and that
    literal is searched in the document's page texts (plan T5). Ground truth for
    "did retrieval put the right *page* in the prompt" (recall@k)."""

    pages_by_path: dict[str, frozenset[Page]]


def build_target_index(
    raws: dict[str, Any], manifest: dict[str, Any], page_texts: dict[str, list[tuple[int, str]]]
) -> TargetIndex:
    """`page_texts`: document title -> [(page_number, text)] (from `document_chunks`)."""
    entries = {e["external_ref"]: e for e in manifest["documents"]}
    pages_by_path: dict[str, set[Page]] = {}
    for file_key, raw in raws.items():
        for doc in raw.get("documents") or []:
            entry = entries.get(doc.get("id"))
            if entry is None:
                continue
            literals: dict[str, str] = entry.get("key_facts_used") or {}
            for field_name, ledger_path in (doc.get("key_facts") or {}).items():
                literal = literals.get(field_name)
                if not literal:
                    continue
                needle = _normalize(str(literal))
                for page_number, text in page_texts.get(entry["title"], []):
                    if needle in _normalize(text):
                        pages_by_path.setdefault(f"{file_key}.{ledger_path}", set()).add(
                            (entry["title"], page_number)
                        )
    return TargetIndex({path: frozenset(pages) for path, pages in pages_by_path.items()})


def target_pages(
    question: ls.Question,
    index: TargetIndex,
    *,
    expected: ExpectedValue | None = None,
    catalog: DocumentCatalog | None = None,
    page_texts: dict[str, list[tuple[int, str]]] | None = None,
) -> frozenset[Page]:
    """Empty when the question has no ledger answer or no document prints that fact
    (then recall is simply not measurable for it — never a pass or a fail).

    Two sources, unioned: (1) the ledger `key_facts` index (T5); (2) when `expected`,
    `catalog` and `page_texts` are given, the expected value's own spellings searched in
    the pages of the question's `required_sources` documents — covers facts that are
    printed but not registered as a key_fact (e.g. a financial-close date on a cover)."""
    if question.expected_answer is None:
        return frozenset()
    ref = question.expected_answer.removeprefix("ledger:")
    pages: set[Page] = set()
    for path, found in index.pages_by_path.items():
        if path == ref or path.startswith(ref + "."):
            pages |= found
    if (
        expected is not None
        and catalog is not None
        and page_texts is not None
        and not expected.skip
    ):
        titles = {
            title
            for name in question.required_sources
            for title in catalog.titles
            if title == name or catalog.title_to_type.get(title) == name
        }
        needles = [_normalize(sp) for group in expected.required for sp in group]
        for title in titles:
            for page_number, text in page_texts.get(title, []):
                haystack = _normalize(text)
                if any(n in haystack for n in needles):
                    pages.add((title, page_number))
    return frozenset(pages)


# ---------------------------------------------------------------- retrieval-only recall


@dataclass(frozen=True)
class RetrievalProbe:
    id: str
    category: str
    ask_as_user: str
    targets: tuple[Page, ...]
    retrieved: tuple[Page, ...]

    @property
    def measurable(self) -> bool:
        return bool(self.targets)

    @property
    def hit(self) -> bool:
        return bool(set(self.targets) & set(self.retrieved))


def render_retrieval_markdown(probes: list[RetrievalProbe], *, top_k: int, label: str) -> str:
    measurable = [p for p in probes if p.measurable]
    hits = sum(1 for p in measurable if p.hit)
    lines = [
        f"# Retrieval recall@{top_k} — {label}",
        "",
        f"Ölçülebilir soru: {len(measurable)}/{len(probes)} (hedef sayfası türetilebilenler) · "
        f"**recall@{top_k}: {hits}/{len(measurable)}"
        f" (%{100.0 * hits / len(measurable) if measurable else 0.0:.1f})**",
        "",
        "| Soru | Kategori | Hedef sayfa(lar) | Prompt'a girdi mi |",
        "|---|---|---|---|",
    ]
    for p in probes:
        if not p.measurable:
            lines.append(f"| {p.id} | {p.category} | – | ölçülemez |")
            continue
        target_text = ", ".join(f"{t} s.{n}" for t, n in sorted(p.targets))
        lines.append(f"| {p.id} | {p.category} | {target_text} | {'✅' if p.hit else '❌'} |")
    return "\n".join(lines) + "\n"


def retrieval_probes_to_json(probes: list[RetrievalProbe]) -> list[dict[str, Any]]:
    return [
        {
            "id": p.id,
            "category": p.category,
            "ask_as_user": p.ask_as_user,
            "targets": [list(t) for t in p.targets],
            "retrieved": [list(r) for r in p.retrieved],
            "measurable": p.measurable,
            "hit": p.hit if p.measurable else None,
        }
        for p in probes
    ]


# ---------------------------------------------------------------- consistency (repeat) report


@dataclass(frozen=True)
class RepeatOutcome:
    """One repetition of one question over the real `/api/ask`, joined with the
    `audit_log.chunks_retrieved` row of that very request."""

    id: str
    repeat: int
    target_in_prompt: bool | None  # None = no target pages derivable
    answered: bool
    value_ok: bool | None  # None = value check skipped/not applicable
    error: str | None


@dataclass(frozen=True)
class ConsistencySummary:
    retrieval_stable: int  # questions whose target_in_prompt agrees across all repeats
    retrieval_measurable: int
    model_answered: int  # repeats with target_in_prompt=True that were answered
    model_measurable: int  # repeats with target_in_prompt=True
    value_ok: int
    value_measurable: int


def summarize_consistency(outcomes: list[RepeatOutcome]) -> ConsistencySummary:
    by_id: dict[str, list[RepeatOutcome]] = {}
    for o in outcomes:
        if o.error is None:
            by_id.setdefault(o.id, []).append(o)
    retrieval_measurable = retrieval_stable = 0
    for rows in by_id.values():
        flags = {r.target_in_prompt for r in rows}
        if None in flags:
            continue
        retrieval_measurable += 1
        if len(flags) == 1:
            retrieval_stable += 1
    with_target = [o for o in outcomes if o.error is None and o.target_in_prompt]
    valued = [o for o in outcomes if o.error is None and o.value_ok is not None]
    return ConsistencySummary(
        retrieval_stable=retrieval_stable,
        retrieval_measurable=retrieval_measurable,
        model_answered=sum(1 for o in with_target if o.answered),
        model_measurable=len(with_target),
        value_ok=sum(1 for o in valued if o.value_ok),
        value_measurable=len(valued),
    )


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} (%{100.0 * num / den:.1f})" if den else "–"


def render_consistency_markdown(outcomes: list[RepeatOutcome], *, label: str) -> str:
    s = summarize_consistency(outcomes)
    lines = [
        f"# Tutarlılık ölçümü — {label}",
        "",
        f"- **Retrieval kararlılığı** (hedef sayfa her tekrarda aynı şekilde girdi/girmedi): "
        f"{_pct(s.retrieval_stable, s.retrieval_measurable)}",
        f"- **Model kararlılığı** (hedef sayfa prompt'tayken cevap verdi): "
        f"{_pct(s.model_answered, s.model_measurable)}",
        f"- **Uçtan uca** (beklenen değer cevapta): {_pct(s.value_ok, s.value_measurable)}",
        "",
        "| Soru | Tekrar | Hedef prompt'ta | Cevapladı | Değer doğru | Hata |",
        "|---|---|---|---|---|---|",
    ]

    def mark(value: bool | None) -> str:
        return "–" if value is None else ("✅" if value else "❌")

    for o in outcomes:
        lines.append(
            f"| {o.id} | {o.repeat} | {mark(o.target_in_prompt)} | {mark(o.answered)} | "
            f"{mark(o.value_ok)} | {o.error or ''} |"
        )
    return "\n".join(lines) + "\n"
