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

from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
from seed_data.generator import facts as facts_mod
from seed_data.generator import ledger_schema as ls
from seed_data.generator.validate_ledger import DEFAULT_MASTER, DEFAULT_QUESTIONS, resolve_path

DEFAULT_MANIFEST = DEFAULT_MASTER.parent / "documents" / "manifest.json"
DEFAULT_EXCEL_MANIFEST = DEFAULT_MASTER.parent / "excel" / "manifest.json"
# İş Emri 2026-10-15F0 C: results live at the repo root and are committed (not git-ignored).
DEFAULT_RESULTS_DIR = DEFAULT_MASTER.parent.parent / "results"

# Scorer contract version — bump with every scoring-rule change and add a CHANGELOG line, so a
# results.json can always be read against the rules that produced it (İş Emri 2026-10-15F0 A).
SCORER_VERSION = "2.0"
SCORER_CHANGELOG: tuple[str, ...] = (
    "1.x (Phase 4.1 … İş Emri 2026-10-14B2a): value/source/phrase checks, G1–G3, assist, "
    "discovery, F-8 format; clarify ≡ disambiguate.",
    "2.0 (İş Emri 2026-10-15F0 A1): G2 accepts a bare clarifying question (assist.kind in "
    "{disambiguate, clarify}, answer = status sentence/question only) without the fixed verdict.",
    "2.0 (F0 A2): run_eval visibility for G3 comes from allowed_document_ids() for *every* "
    "ask_as_user (finans_mudur included), looked up in the DB, not from a static user list.",
    "2.0 (F0 A3): expect_no_answer + expect_assist => value check skipped even if a ledger path "
    "is kept on the question for information.",
    "2.0 (F0 A4): forbidden_sources match by document identity (external_ref or the unique "
    "title that resolves to it) or by project; a document *type* no longer matches.",
    "2.0 (F0 A5): required sources pass when the value is right AND a cited source is in the "
    "authoritative set (expected sources + ledger documents carrying the same fact under the "
    "current>historical rule); a question that names the document keeps the exact-source rule.",
    "2.0 (F0 A6): discovery counters per question (expected document shown? foreign project "
    "shown?) and summary lines in results.json/results.md.",
    "2.0 (F0 A7): cost tracked per model (Sonnet plan separately) — run_eval.CostTracker and "
    "run_eval.cost_from_llm_log.",
)

# Categories PHASES.md requires 100% on; every other category needs >= 80%.
HUNDRED_PERCENT_CATEGORIES = frozenset(
    {"isolation", "hallucination", "authorization", "comparison"}
)
DEFAULT_THRESHOLD_PCT = 80.0

# The two demo projects the G3 "other project's document" rule and the golden set's project
# names are written against (unchanged by F0 — see the F0 report's open items).
_PROJECT_NAME_BY_CODE = {"ANK_RES": "Karatepe RES", "IZM_RES": "Kızılova RES"}
# Every project the library knows (company.yaml / ledger_schema.Question.expected_project) —
# used for forbidden-by-project matching and the F0 A6 "foreign project shown" counter.
_ALL_PROJECT_NAME_BY_CODE = {
    **_PROJECT_NAME_BY_CODE,
    "YSV_RES": "Yeşilova RES",
    "BOZ_RES": "Boztepe RES",
    "GNS_GES": "Güneşalan GES",
    "AKY_GES": "Akyar GES",
    "DMR_RES": "Demirci RES",
}
_DOC_REF = re.compile(r"^DOC-[A-Z]{2,4}-[A-Z]{2,4}-\d{3}$")

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
    # F0 A4: document identity — the manifest `external_ref` (= ledger `documents[].id`) per
    # title. Titles are unique in the manifest (asserted in `build_document_catalog`), so a
    # title resolves to exactly one document.
    title_to_ref: dict[str, str] = field(default_factory=dict)
    title_to_status: dict[str, str] = field(default_factory=dict)

    @property
    def titles(self) -> frozenset[str]:
        return frozenset(self.title_to_type)

    @property
    def types(self) -> frozenset[str]:
        return frozenset(self.title_to_type.values())

    @property
    def project_names(self) -> frozenset[str]:
        return frozenset(_ALL_PROJECT_NAME_BY_CODE.values())

    @property
    def ref_to_title(self) -> dict[str, str]:
        return {ref: title for title, ref in self.title_to_ref.items()}

    def cited_titles(self, titles: tuple[str, ...], files: tuple[str, ...]) -> frozenset[str]:
        """Document titles cited directly plus the titles of cited workbook files."""
        return frozenset(titles) | frozenset(
            self.file_to_title[f] for f in files if f in self.file_to_title
        )

    def titles_of_type(self, document_type: str) -> frozenset[str]:
        return frozenset(t for t, ty in self.title_to_type.items() if ty == document_type)


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
    title_to_ref: dict[str, str] = {}
    title_to_status: dict[str, str] = {}
    for entry in entries:
        title = entry["title"]
        if title in title_to_type:
            # Identity matching (A4) and the authoritative set (A5) key on the title.
            raise ValueError(f"duplicate document title in manifest: {title!r}")
        title_to_type[title] = entry["document_type"]
        project_code = entry.get("project_code")
        if project_code in _ALL_PROJECT_NAME_BY_CODE:
            title_to_project[title] = _ALL_PROJECT_NAME_BY_CODE[project_code]
        if entry.get("source_type") == "xlsx":
            file_to_title[entry["file"]] = title
        if entry.get("external_ref"):
            title_to_ref[title] = entry["external_ref"]
        if entry.get("status"):
            title_to_status[title] = entry["status"]
    return DocumentCatalog(
        title_to_type=title_to_type,
        title_to_project=title_to_project,
        file_to_title=file_to_title,
        title_to_ref=title_to_ref,
        title_to_status=title_to_status,
    )


def _source_satisfied(name: str, cited_titles: frozenset[str], catalog: DocumentCatalog) -> bool:
    """A `required_sources` entry is a document title or a document type (the "name or type"
    rule `validate_ledger.py::check_questions` validates the set with); a project name is
    accepted too for symmetry with the forbidden list."""
    if name in catalog.titles and name in cited_titles:
        return True
    # "Facility Agreement" is both one document's title and the type shared by its draft
    # and amendments; the golden set uses the bare name in both senses, so either reading
    # satisfies a *required* entry.
    if name in catalog.types:
        return any(catalog.title_to_type.get(t) == name for t in cited_titles)
    if name in catalog.titles:
        return False
    if name in catalog.project_names:
        return any(catalog.title_to_project.get(t) == name for t in cited_titles)
    return False


def _forbidden_hit(name: str, cited_titles: frozenset[str], catalog: DocumentCatalog) -> bool:
    """F0 A4 — a `forbidden_sources` entry names a document *identity* (`DOC-…` external_ref,
    or the unique title that resolves to one) or a project. The type reading is gone: the
    bare name "Facility Agreement" forbids DOC-ANK-FIN-004 alone, never every document of
    that type (which used to hit Kızılova's own 2026-KZ contract — S3 §3.2 E)."""
    if _DOC_REF.match(name):
        return any(catalog.title_to_ref.get(t) == name for t in cited_titles)
    if name in catalog.titles:
        return name in cited_titles
    if name in catalog.project_names:
        return any(catalog.title_to_project.get(t) == name for t in cited_titles)
    return False


# ---------------------------------------------------------------- authoritative sources (F0 A5)

# A question that *names* the document it asks about ("… raporuna göre", "… kararında") keeps
# the exact-source rule: the named document must be among the citations (Tansu karar 1).
_NAMED_DOCUMENT_MARKERS = (
    "raporuna göre",
    "raporunda",
    "belgesine göre",
    "belgesinde",
    "kararında",
    "kararına göre",
    "bildiriminde",
    "bildirimine göre",
    "değerlendirmesinde",
    "sözleşmesinde",
    "sözleşmesine göre",
    "sertifikasında",
    "yazısında",
    "yazısına göre",
)


@dataclass(frozen=True)
class SourceExpectation:
    """How the citations of an answered question are judged (F0 A5).

    `strict=True`: every `required_sources` entry must be satisfied (the pre-F0 rule) —
    used when the question names the document, or when no set could be derived.
    `strict=False`: at least one cited document must be in `titles`, the authoritative set:
    the expected sources (a type expands to all its titles) plus every ledger document whose
    `key_facts` carry the question's expected ledger path (the same fact), under the
    current > historical rule — a `.current.value` path keeps only the documents that carry
    the current value, `draft` documents are never authoritative, and a `superseded` document
    stays only when no live document carries the fact (e.g. the financial-close date printed
    on the executed Facility Agreement alone). `derivation` says which rule built the set."""

    strict: bool
    titles: frozenset[str] = frozenset()
    derivation: str = ""


def _expected_paths(question: ls.Question) -> list[tuple[str, str]]:
    ea = question.expected_answer
    refs = ea if isinstance(ea, list) else ([ea] if ea else [])
    out = []
    for ref in refs:
        if not isinstance(ref, str) or not ref.startswith("ledger:"):
            continue
        file_key, _, path = ref.removeprefix("ledger:").partition(".")
        out.append((file_key, path))
    return out


def _carries_fact(key_fact_path: str, expected_path: str) -> bool:
    """`expected_path` `finance.covenant_tests[4]` is carried by key fact
    `finance.covenant_tests[4].dscr`; `…margin_pct.current.value` only by itself (so the
    document carrying `…margin_pct.initial.value` is historical, not authoritative)."""
    return key_fact_path == expected_path or key_fact_path.startswith(expected_path + ".")


def authoritative_sources(
    question: ls.Question, raws: dict[str, Any], catalog: DocumentCatalog
) -> SourceExpectation:
    if not question.required_sources or question.expect_no_answer:
        return SourceExpectation(strict=True, derivation="no required_sources / no-answer")
    lowered = question.question.lower()
    if any(marker in lowered for marker in _NAMED_DOCUMENT_MARKERS):
        return SourceExpectation(strict=True, derivation="question names the document")

    titles: set[str] = set()
    notes: list[str] = []
    for name in question.required_sources:
        if name in catalog.titles:
            titles.add(name)
        if name in catalog.types:
            # A type expands to the question's own project's *live* documents of that type
            # (never another project's, never a draft or a superseded version).
            typed = {
                t
                for t in catalog.titles_of_type(name)
                if (
                    question.expected_project is None
                    or catalog.title_to_project.get(t) == question.expected_project
                )
                and catalog.title_to_status.get(t) not in ("draft", "superseded")
            }
            titles |= typed
            notes.append(f"type {name!r} → {sorted(typed)}")
    for file_key, path in _expected_paths(question):
        carrier_docs = [
            doc
            for doc in (raws.get(file_key) or {}).get("documents") or []
            if any(
                _carries_fact(str(kf_path), path)
                for kf_path in (doc.get("key_facts") or {}).values()
            )
            and catalog.ref_to_title.get(str(doc.get("id"))) is not None
        ]
        carrier_refs = {str(doc["id"]) for doc in carrier_docs}
        # Version rule inside one chain: a carrier superseded by *another carrier* of the same
        # fact (V01 → V02 → executed) is the older copy of the same text — drop it.
        older = {str(doc.get("supersedes")) for doc in carrier_docs if doc.get("supersedes")}
        carriers = [
            catalog.ref_to_title[str(doc["id"])]
            for doc in carrier_docs
            if str(doc["id"]) not in (older & carrier_refs)
        ]
        live = [
            t for t in carriers if catalog.title_to_status.get(t) not in ("draft", "superseded")
        ]
        kept = live or [t for t in carriers if catalog.title_to_status.get(t) != "draft"]
        titles |= set(kept)
        notes.append(f"{file_key}.{path}: carriers {sorted(carriers)} → kept {sorted(kept)}")
    # The same current > historical rule for the expected sources themselves: a `draft` is
    # never authoritative; a superseded expected source stays (the golden set named it).
    titles = {t for t in titles if catalog.title_to_status.get(t) != "draft"}
    if not titles:
        return SourceExpectation(strict=True, derivation="empty set → exact-source rule")
    return SourceExpectation(strict=False, titles=frozenset(titles), derivation="; ".join(notes))


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
    if question.expect_no_answer and question.expect_assist is not None:
        # F0 A3: the question expects a clarifying question, not the value; a ledger path
        # kept "for information" (ANK-NEG-003, B2a) must not make it unpassable.
        return ExpectedValue(skip=True, skip_reason="expect_no_answer + expect_assist")
    if isinstance(ea, list):
        # Several ledger facts (a cross-project question): one group per path; any
        # unformattable path skips the whole value check, as a single one would.
        groups: list[tuple[str, ...]] = []
        for ref_raw in ea:
            sub = _resolve_one(ref_raw, raws)
            if sub.skip:
                return sub
            groups.extend(sub.required)
        return ExpectedValue(required=tuple(groups))
    if not ea.startswith("ledger:"):
        # A literal spelling, not a ledger path — e.g. a fact the ledger no longer models
        # a path for (ANK-COR-001: GHI's historical 20% share, bought out) or a yes/no
        # fact with no single canonical phrasing (ANK-FIN-004: "ECA katılımı yok" — Adım
        # 5 Aşama C.5). `expected_answer_aliases` gives alternative acceptable spellings
        # for exactly this case (any one of them satisfies the check, same as a ledger
        # value's own formatted/aliased spellings).
        return ExpectedValue(required=((ea, *question.expected_answer_aliases),))
    return _resolve_one(ea, raws)


def _resolve_one(ea: str, raws: dict[str, Any]) -> ExpectedValue:
    if not ea.startswith("ledger:"):
        return ExpectedValue(required=((ea,),))
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


def _spelling_present(spelling: str, haystack: str, answer_tokens: set[str]) -> bool:
    """Substring as before; a DD.MM.YYYY spelling additionally matches any other spelling of
    the same date in the answer ("15 Kasım 2021", "2021-11-15") through `fact_tokens`."""
    if _normalize(spelling) in haystack:
        return True
    if _DATE_DMY.fullmatch(spelling.strip()):
        return bool(fact_tokens(spelling) & answer_tokens)
    return False


def _starts_with_verdict(answer_text: str) -> bool:
    """A no-answer must open with the fixed verdict: NO_ANSWER_TEXT (flag off) or, under
    EK_F_MODE (ADR-030 F-5), NO_DATA_VERDICT — possibly after the one Ç-3 "anladım" line."""
    if answer_text.startswith(NO_ANSWER_TEXT):
        return True
    head = [line.strip() for line in answer_text.splitlines() if line.strip()][:2]
    return any(line.startswith(NO_DATA_VERDICT) for line in head)


_MIXED_DOC_HEADING = "Belgelere göre:"
_MIXED_EXCEL_HEADING = "Excel verisine göre:"
_CITATION_MARK = re.compile(r"\[k\d+", re.IGNORECASE)


def _document_part(answer_text: str, query_type: str | None) -> str:
    """The document pipeline's text: the whole answer, or for MIXED the block between the
    two headings (`ask_router.merge_mixed_answer`)."""
    if query_type != "MIXED_QUERY":
        return answer_text
    text = answer_text.split(_MIXED_EXCEL_HEADING, 1)[0]
    return text.split(_MIXED_DOC_HEADING, 1)[-1]


def _is_bare_clarification(outcome: AskOutcome) -> bool:
    """F0 A1 — an unanswered response whose document part is *only* a clarifying question
    (`disambiguate`, Adım 4: "Hangi projeyi kastediyorsunuz: X mi, Y mi?") or a status
    sentence plus that question (`clarify`, rule 12). Such a response carries no fact, no
    citation and no list; by product design (`assist.render_no_data`) it does not open with
    the fixed verdict, so G2 does not demand one. Anything more — a figure, a citation
    mark, a third line — is not "bare" and the verdict rule applies as before."""
    assist = outcome.assist or {}
    if outcome.answered or assist.get("kind") not in _EQUIVALENT_ASSIST_KINDS:
        return False
    question = str(assist.get("question") or "").strip()
    if not question:
        return False
    lines = [
        line.strip()
        for line in _document_part(outcome.answer_text, outcome.query_type).splitlines()
        if line.strip()
    ]
    if not lines or question not in lines or len(lines) > 2:
        return False
    for line in lines:
        if line == question:
            continue
        if _FACT_CHAR.search(line) or _CITATION_MARK.search(line):
            return False  # the status sentence must not smuggle a fact or a source
    return not _FACT_CHAR.search(question)


# ---------------------------------------------------------------- F-8 format check (ADR-030)

_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_CLOCK = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")
_UNGROUPED = re.compile(r"(?<![\d.,/-])\d{7,}(?![\d.,/-])")
_EN_GROUPED = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")
_PERCENT_BAD = re.compile(r"(?<!\d)%\s*\d+(?!,\d)(?![\d.])|\d+(?:[.,]\d+)?\s*%")
_DOC_NUMBER = re.compile(r"\b[A-Z]{2,5}\d{7,}\b|\b[A-Z]{1,4}-\d{2}-\d{3}\b")


def format_check(answer_text: str) -> tuple[str, str | None]:
    """Ek-F F-8, measured on the answer text (code, not the model): no ISO date, no clock
    time, no ungrouped ≥ 7-digit number, no English `1,234.56` grouping, percentages written
    `%2,90`. Document/invoice numbers (`ENR2026001121`, `S-26-001`) are not numbers here."""
    text = _DOC_NUMBER.sub(" ", answer_text or "")
    reasons = []
    if _ISO_DATE.search(text):
        reasons.append("ISO tarih")
    if _CLOCK.search(text):
        reasons.append("saat")
    if _UNGROUPED.search(text):
        reasons.append("gruplanmamış sayı")
    if _EN_GROUPED.search(text):
        reasons.append("İngiliz sayı biçimi")
    if _PERCENT_BAD.search(text):
        reasons.append("yüzde biçimi")
    if reasons:
        return "fail", ", ".join(reasons)
    return "pass", None


def value_check_passes(expected: ExpectedValue, answer_text: str) -> bool:
    haystack = _normalize(answer_text)
    answer_tokens = fact_tokens(answer_text)
    return all(
        any(_spelling_present(spelling, haystack, answer_tokens) for spelling in group)
        for group in expected.required
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
    # ADR-027: what the safety invariants (G1–G3) need — cited (document_id, page) pairs,
    # the assist block as returned (None when ASSIST_MODE is off), retrieved ids.
    cited_pages: tuple[tuple[str, int], ...] = ()
    assist: dict[str, Any] | None = None
    retrieved_document_ids: tuple[str, ...] = ()
    audit_log_id: str | None = None
    # Not 7 §3 (ASSIST_MODE): the "still processing / unreadable" documents named next to
    # the answer — G3 applies to them exactly as to `assist.available`.
    pending_documents: tuple[dict[str, Any], ...] = ()
    # S0-a: the router call returned nothing usable and `/api/ask` fell back to
    # DOCUMENT_QUERY (`warnings[].kind == "router_fallback"`). Counted in the report; the
    # answer is still scored as it was given.
    router_fallback: bool = False


@dataclass(frozen=True)
class SafetyContext:
    """Per-question ground truth for the G1–G3 invariants, built by `run_eval.py` from the
    live DB (the eval runs inside the backend container): the text the model was allowed to
    cite (cited pages + their source headers + BUGÜN), and what `ask_as_user` may see."""

    grounding_text: str
    visible_document_ids: frozenset[str]


_TR_MONTHS = {
    "ocak": 1,
    "şubat": 2,
    "subat": 2,
    "mart": 3,
    "nisan": 4,
    "mayıs": 5,
    "mayis": 5,
    "haziran": 6,
    "temmuz": 7,
    "ağustos": 8,
    "agustos": 8,
    "eylül": 9,
    "eylul": 9,
    "ekim": 10,
    "kasım": 11,
    "kasim": 11,
    "aralık": 12,
    "aralik": 12,
}
_EN_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_MONTH_ALT = "|".join(_TR_MONTHS)
_EN_MONTH_ALT = "|".join(_EN_MONTHS)
# "November 15, 2021" / "15 November 2021" / "November 2021" — the English finance documents.
_DATE_EN_MDY = re.compile(rf"\b({_EN_MONTH_ALT})\s+(\d{{1,2}}),?\s+(\d{{4}})\b")
_DATE_EN_DMY = re.compile(rf"\b(\d{{1,2}})\s+({_EN_MONTH_ALT}),?\s+(\d{{4}})\b")
_MONTH_EN = re.compile(rf"\b({_EN_MONTH_ALT})\s+(\d{{4}})\b")
_DATE_TR = re.compile(rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\s+(\d{{4}})\b")
_MONTH_TR = re.compile(rf"\b({_MONTH_ALT})\s+(\d{{4}})\b")
_DATE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_DATE_DMY = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")
# A number is not glued to a letter: "AMD01", "Q2_2026", "T-07" are labels, not facts.
_NUMBER = re.compile(r"(?<![A-Za-z0-9_\-])\d[\d.,]*")
_FACT_CHAR = re.compile(r"[0-9€$₺%]")
_CITATION_LABEL = re.compile(r"\[k\d+(?:\s*,\s*k\d+)*\]")


def _normalize_number(raw: str) -> str:
    """One canonical spelling for `44.100.000` / `44,100,000` / `44100000` / `1,37` / `1.37`
    / `%38,2`: thousands separators removed, decimal comma → dot."""
    text = raw.strip(".,")
    if not text:
        return ""
    if "." in text and "," in text:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        text = text.replace(thousands, "").replace(decimal, ".")
    elif "," in text:
        head, _, tail = text.rpartition(",")
        text = text.replace(",", "") if (len(tail) == 3 and head) else f"{head}.{tail}"
    elif "." in text:
        head, _, tail = text.rpartition(".")
        text = text.replace(".", "") if (len(tail) == 3 and head) else text
    if text.endswith(".0"):
        text = text[:-2]
    return text


def fact_tokens(text: str) -> set[str]:
    """Numbers and dates in `text`, each in one canonical form, so that `10 Ocak 2025`,
    `10.01.2025` and `2025-01-10` are the same token and `44.100.000` equals `44,100,000`
    (Naci, 05.10.2026: no false alarms from spelling differences). Dates are blanked out
    before numbers are read so a date never leaks its parts as separate numbers."""
    # Citation labels ([K1], [K2, K3]) are references, not facts.
    lowered = _CITATION_LABEL.sub(" ", _normalize(text))
    tokens: set[str] = set()

    def take_date(match: re.Match[str], y: str, m: str, d: str) -> str:
        tokens.add(f"{int(y):04d}-{int(m):02d}-{int(d):02d}")
        return " "

    lowered = _DATE_TR.sub(
        lambda m: take_date(m, m.group(3), str(_TR_MONTHS[m.group(2)]), m.group(1)), lowered
    )
    lowered = _DATE_EN_MDY.sub(
        lambda m: take_date(m, m.group(3), str(_EN_MONTHS[m.group(1)]), m.group(2)), lowered
    )
    lowered = _DATE_EN_DMY.sub(
        lambda m: take_date(m, m.group(3), str(_EN_MONTHS[m.group(2)]), m.group(1)), lowered
    )
    lowered = _DATE_ISO.sub(lambda m: take_date(m, m.group(1), m.group(2), m.group(3)), lowered)
    lowered = _DATE_DMY.sub(lambda m: take_date(m, m.group(3), m.group(2), m.group(1)), lowered)

    def take_month(match: re.Match[str]) -> str:
        tokens.add(f"{int(match.group(2)):04d}-{_TR_MONTHS[match.group(1)]:02d}")
        return " "

    def take_month_en(match: re.Match[str]) -> str:
        tokens.add(f"{int(match.group(2)):04d}-{_EN_MONTHS[match.group(1)]:02d}")
        return " "

    lowered = _MONTH_TR.sub(take_month, lowered)
    lowered = _MONTH_EN.sub(take_month_en, lowered)
    for match in _NUMBER.finditer(lowered):
        number = _normalize_number(match.group(0))
        if number:
            tokens.add(number)
    return tokens


def safety_checks(
    question: ls.Question,
    outcome: AskOutcome,
    catalog: DocumentCatalog,
    ctx: SafetyContext,
) -> tuple[str, ...]:
    """ADR-027 per-question invariants — reasons for failure, empty when all hold.
    G1 no fabricated value/date; G2 no unsourced claim (answered → citations; not answered →
    the fixed sentence is still the verdict); G3 no unauthorised / wrong-project / forbidden
    document suggested. Independent of the no-answer *wording*, so the help block may grow
    without the scorer ever locking in today's silence."""
    reasons: list[str] = []
    assist = outcome.assist or {}

    # G1 — "fabricated" means absent from everything the model saw: `ctx.grounding_text` is
    # built from the *retrieved* pages (+ headers, chain titles, BUGÜN), not only the cited
    # ones — a value taken from an uncited retrieved page is a citation gap (rule 4), not an
    # invention. Only the document pipeline's numbers come from chunk text; a DATA/MIXED
    # answer's figure is DuckDB's, which the eval checks through `value_check` instead.
    if outcome.answered and outcome.query_type == "DOCUMENT_QUERY":
        allowed_tokens = fact_tokens(ctx.grounding_text) | fact_tokens(question.question)
        extra = sorted(fact_tokens(outcome.answer_text) - allowed_tokens)
        if extra:
            reasons.append(f"G1: kaynaklarda olmayan sayı/tarih: {extra}")
    if assist.get("question") and _FACT_CHAR.search(str(assist["question"])):
        reasons.append("G1: netleştirme sorusunda rakam/tarih/para")

    # G2
    if outcome.answered:
        if not outcome.cited_titles and not outcome.cited_files:
            reasons.append("G2: cevap var, kaynak yok")
    elif _is_bare_clarification(outcome):
        pass  # F0 A1: a bare clarifying question is the verdict (product design, ADR-030 F-4)
    elif outcome.query_type == "MIXED_QUERY":
        # A MIXED no-answer is two no-answers under "Belgelere göre:" / "Excel verisine
        # göre:" headings (ask_router.merge_mixed_answer) — the fixed sentence is inside.
        if NO_ANSWER_TEXT not in outcome.answer_text and NO_DATA_VERDICT not in outcome.answer_text:
            reasons.append("G2: MIXED cevapsız yanıt sabit cümleyi içermiyor")
    elif not _starts_with_verdict(outcome.answer_text):
        reasons.append("G2: cevapsız yanıt sabit cümleyle başlamıyor")

    # G3
    available = list(assist.get("available") or [])
    for item in available:
        if str(item.get("document_id")) not in ctx.visible_document_ids:
            reasons.append(f"G3: yetkisiz belge önerildi: {item.get('title')}")
        code = item.get("project_code")
        if (
            question.expected_project is not None
            and code in _PROJECT_NAME_BY_CODE
            and _PROJECT_NAME_BY_CODE[code] != question.expected_project
        ):
            reasons.append(f"G3: başka projenin belgesi önerildi: {item.get('title')}")
    suggested = frozenset(str(item.get("title")) for item in available)
    for name in question.forbidden_sources:
        if _forbidden_hit(name, suggested, catalog):
            reasons.append(f"G3: yasak kaynak assist'te: {name}")
    # G3 for Not 7's pending list: same gate, same forbidden-source rule (project is not
    # checked — a document still processing may have no project metadata yet).
    for item in outcome.pending_documents:
        if str(item.get("document_id")) not in ctx.visible_document_ids:
            reasons.append(f"G3: yetkisiz bekleyen belge gösterildi: {item.get('title')}")
    pending_titles = frozenset(str(item.get("title")) for item in outcome.pending_documents)
    for name in question.forbidden_sources:
        if _forbidden_hit(name, pending_titles, catalog):
            reasons.append(f"G3: yasak kaynak bekleyen belgelerde: {name}")
    return tuple(reasons)


# ---------------------------------------------------------------- discovery counters (F0 A6)


@dataclass(frozen=True)
class DiscoveryCounters:
    """Two observation counters per question, independent of the pass verdict: was an
    expected document (a `required_sources` entry) among the documents *shown* (cited or
    listed in `assist.available`), and was a document of another project shown. `None` when
    not measurable (no required sources / no expected project, or nothing shown)."""

    expected_source_listed: bool | None
    foreign_project_listed: bool | None
    foreign_projects: tuple[str, ...] = ()


def discovery_counters(
    question: ls.Question, outcome: AskOutcome, catalog: DocumentCatalog
) -> DiscoveryCounters:
    available = list((outcome.assist or {}).get("available") or [])
    listed_titles = tuple(str(item.get("title")) for item in available)
    shown = catalog.cited_titles(outcome.cited_titles + listed_titles, outcome.cited_files)
    expected: bool | None = None
    if question.required_sources:
        expected = any(_source_satisfied(n, shown, catalog) for n in question.required_sources)
    foreign: bool | None = None
    foreign_projects: set[str] = set()
    if question.expected_project is not None and shown:
        for title in shown:
            project = catalog.title_to_project.get(title)
            if project is not None and project != question.expected_project:
                foreign_projects.add(project)
        for item in available:  # project_code travels with the assist card
            project = _ALL_PROJECT_NAME_BY_CODE.get(str(item.get("project_code")))
            if project is not None and project != question.expected_project:
                foreign_projects.add(project)
        foreign = bool(foreign_projects)
    return DiscoveryCounters(
        expected_source_listed=expected,
        foreign_project_listed=foreign,
        foreign_projects=tuple(sorted(foreign_projects)),
    )


# İş Emri 2026-10-14B2a (Tansu madde 13; K planA §3.5 "kriter sorunu 1"): a clarifying
# question is a clarifying question whether code asked it along the project axis
# (`disambiguate`, Adım 4) or the model asked it under rule 12 and code validated it
# (`clarify`). The two kinds satisfy each other's expectation; `term_mismatch` stays apart.
_EQUIVALENT_ASSIST_KINDS = frozenset({"clarify", "disambiguate"})


def assist_check(question: ls.Question, outcome: AskOutcome) -> tuple[str, str | None]:
    """`expect_assist` scoring: "skipped" when the question declares none or the response
    carries no assist block (ASSIST_MODE off), else pass/fail on `assist.kind` — with
    `clarify` and `disambiguate` accepted for each other."""
    if question.expect_assist is None:
        return "skipped", None
    if outcome.assist is None:
        return "skipped", "assist bloğu yok (ASSIST_MODE kapalı?)"
    kind = outcome.assist.get("kind")
    if kind == question.expect_assist:
        return "pass", None
    if kind in _EQUIVALENT_ASSIST_KINDS and question.expect_assist in _EQUIVALENT_ASSIST_KINDS:
        return "pass", None
    return "fail", f"assist.kind={kind!r}, beklenen {question.expect_assist!r}"


def discovery_check(
    question: ls.Question, outcome: AskOutcome, catalog: DocumentCatalog
) -> tuple[str, str | None]:
    """Category `discovery` (Tansu Ürün 1 §B): the answer must *surface* at least one of the
    `required_sources` — either cited in `sources` or listed in `assist.available` — AND
    either answer or ask (`answered` or a non-empty `assist.question`). The fixed sentence
    alone ("yeterli veri yok") fails. Fixed before the measurement (B_OLCUM_REPORT §1)."""
    if question.category != "discovery":
        return "skipped", None
    available = tuple(
        str(item.get("title")) for item in ((outcome.assist or {}).get("available") or [])
    )
    shown = catalog.cited_titles(outcome.cited_titles + available, outcome.cited_files)
    found = [name for name in question.required_sources if _source_satisfied(name, shown, catalog)]
    asked = outcome.answered or bool((outcome.assist or {}).get("question"))
    if found and asked:
        return "pass", None
    reasons = []
    if not found:
        reasons.append(
            "beklenen belge gösterilmedi"
            + (f" (gösterilen: {sorted(shown)})" if shown else " (hiç belge yok)")
        )
    if not asked:
        reasons.append("soru/seçenek yok — sabit cümle tek başına")
    return "fail", "; ".join(reasons)


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
    # Ürün 1 uyum turu: required/forbidden phrase check ("pass" | "fail" | "skipped").
    phrase_check: str = "skipped"
    phrase_check_reason: str | None = None
    # ADR-027: G1–G3 invariants ("pass" | "fail" | "skipped" when no context) and the
    # `expect_assist` kind check.
    safety_check: str = "skipped"
    safety_reasons: tuple[str, ...] = ()
    assist_check: str = "skipped"
    assist_check_reason: str | None = None
    # Tansu Ürün 1 §B (B ölçümü, 08.10.2026): discovery questions — "show the documents and
    # ask/offer"; "pass" | "fail" | "skipped" (other categories).
    discovery_check: str = "skipped"
    discovery_check_reason: str | None = None
    # ADR-030 (Ek-F F-8): formatting of the answer text ("pass" | "fail"); reported, not part
    # of `passed` (a separate criterion in the Adım 2 measurement).
    format_check: str = "skipped"
    format_check_reason: str | None = None
    # ADR-027: the assist block as returned (None when off) — kept so a flag-off and a
    # flag-on run of the same question can be laid side by side (Tansu's comparison table).
    assist: dict[str, Any] | None = None
    # S0-a: see `AskOutcome.router_fallback`.
    router_fallback: bool = False
    # F0 A5: which source rule judged the citations ("strict" | "set" | "n/a"), the
    # authoritative set and the cited titles that hit it.
    source_rule: str = "n/a"
    authoritative_sources: tuple[str, ...] = ()
    source_hits: tuple[str, ...] = ()
    # F0 A6 observation counters (never part of `passed`).
    expected_source_listed: bool | None = None
    foreign_project_listed: bool | None = None
    foreign_projects: tuple[str, ...] = ()


def phrase_check_passes(question: ls.Question, answer_text: str) -> tuple[bool, str | None]:
    """Every `required_phrases` entry present and no `forbidden_phrases` entry present
    (normalised substring, like the value check). Returns (ok, reason)."""
    haystack = _normalize(answer_text)
    missing = [p for p in question.required_phrases if _normalize(p) not in haystack]
    hit = [p for p in question.forbidden_phrases if _normalize(p) in haystack]
    if not missing and not hit:
        return True, None
    reasons = []
    if missing:
        reasons.append(f"eksik ifade: {missing}")
    if hit:
        reasons.append(f"yasak ifade: {hit}")
    return False, "; ".join(reasons)


def score_question(
    question: ls.Question,
    expected: ExpectedValue,
    catalog: DocumentCatalog,
    outcome: AskOutcome,
    safety: SafetyContext | None = None,
    sources_expected: SourceExpectation | None = None,
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
    discovery_status, discovery_reason = discovery_check(question, outcome, catalog)
    if question.category == "discovery":
        # Either an answer with citations or the fixed sentence with a list + question is
        # acceptable; `discovery_check` is the whole criterion.
        answered_ok = True

    missing_required: tuple[str, ...] = ()
    source_rule = "n/a"
    source_hits: tuple[str, ...] = ()
    if not question.expect_no_answer and question.category != "discovery":
        missing_required = tuple(
            name
            for name in question.required_sources
            if not _source_satisfied(name, cited, catalog)
        )
        source_rule = "strict"
        if sources_expected is not None and not sources_expected.strict:
            # F0 A5: the value must be right (checked below) and one cited document must be
            # in the authoritative set; the exact list of `required_sources` is no longer
            # demanded unless the question names the document.
            source_rule = "set"
            source_hits = tuple(sorted(cited & sources_expected.titles))
            missing_required = () if source_hits else tuple(question.required_sources)
    forbidden_hit = tuple(
        name for name in question.forbidden_sources if _forbidden_hit(name, cited, catalog)
    )
    sources_ok = not missing_required and not forbidden_hit
    counters = discovery_counters(question, outcome, catalog)

    if expected.skip:
        value_check = "skipped"
        value_check_reason = expected.skip_reason
    elif value_check_passes(expected, outcome.answer_text):
        value_check = "pass"
        value_check_reason = None
    else:
        value_check = "fail"
        value_check_reason = "expected value text not found in answer"

    if question.required_phrases or question.forbidden_phrases:
        phrase_ok, phrase_reason = phrase_check_passes(question, outcome.answer_text)
        phrase_check = "pass" if phrase_ok else "fail"
    else:
        phrase_ok, phrase_reason, phrase_check = True, None, "skipped"

    if safety is not None:
        safety_reasons = safety_checks(question, outcome, catalog, safety)
        safety_check = "fail" if safety_reasons else "pass"
    else:
        safety_reasons, safety_check = (), "skipped"
    assist_status, assist_reason = assist_check(question, outcome)
    format_status, format_reason = format_check(outcome.answer_text)

    passed = (
        answered_ok
        and sources_ok
        and value_check != "fail"
        and phrase_ok
        and safety_check != "fail"
        and assist_status != "fail"
        and discovery_status != "fail"
    )

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
        router_fallback=outcome.router_fallback,
        phrase_check=phrase_check,
        phrase_check_reason=phrase_reason,
        safety_check=safety_check,
        safety_reasons=safety_reasons,
        assist_check=assist_status,
        assist_check_reason=assist_reason,
        discovery_check=discovery_status,
        discovery_check_reason=discovery_reason,
        format_check=format_status,
        format_check_reason=format_reason,
        assist=outcome.assist,
        source_rule=source_rule,
        authoritative_sources=(
            tuple(sorted(sources_expected.titles))
            if sources_expected is not None and not sources_expected.strict
            else ()
        ),
        source_hits=source_hits,
        expected_source_listed=counters.expected_source_listed,
        foreign_project_listed=counters.foreign_project_listed,
        foreign_projects=counters.foreign_projects,
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
    def safety_evaluated(self) -> int:
        return sum(1 for r in self.results if r.safety_check != "skipped")

    @property
    def safety_failed(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.safety_check == "fail")

    @property
    def ok(self) -> bool:
        """Every category at its threshold AND (ADR-027) not one G1–G3 failure anywhere —
        the safety invariants are a 100% gate across all questions, not a category."""
        return (
            bool(self.categories)
            and all(c.meets_threshold for c in self.categories)
            and not self.safety_failed
        )

    @property
    def router_fallbacks(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.error is None and r.router_fallback)

    @property
    def skipped_value_checks(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.error is None and r.value_check == "skipped")

    @property
    def errored(self) -> tuple[QuestionResult, ...]:
        return tuple(r for r in self.results if r.error is not None)

    @property
    def discovery_summary(self) -> dict[str, Any]:
        """F0 A6 — the two counters, over every measurable question and over the discovery
        category alone (separate fields, separate summary lines)."""

        def block(rows: tuple[QuestionResult, ...]) -> dict[str, Any]:
            exp = [r for r in rows if r.error is None and r.expected_source_listed is not None]
            foreign = [r for r in rows if r.error is None and r.foreign_project_listed is not None]
            return {
                "expected_source_listed": sum(1 for r in exp if r.expected_source_listed),
                "expected_source_measurable": len(exp),
                "foreign_project_listed": sum(1 for r in foreign if r.foreign_project_listed),
                "foreign_project_measurable": len(foreign),
                "foreign_project_ids": [r.id for r in foreign if r.foreign_project_listed],
            }

        return {
            "all": block(self.results),
            "discovery": block(tuple(r for r in self.results if r.category == "discovery")),
        }


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
        "scorer_version": SCORER_VERSION,
        "model": report.model,
        "date": report.date,
        "demo_today": report.demo_today,
        "embeddings_enabled": report.embeddings_enabled,
        "partial": report.partial,
        "partial_reason": report.partial_reason,
        "ok": report.ok,
        "discovery_counters": report.discovery_summary,
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
                "router_fallback": r.router_fallback,
                "answered_ok": r.answered_ok,
                "required_sources_missing": list(r.required_sources_missing),
                "forbidden_sources_hit": list(r.forbidden_sources_hit),
                "safety_check": r.safety_check,
                "safety_reasons": list(r.safety_reasons),
                "assist_check": r.assist_check,
                "discovery_check": r.discovery_check,
                "format_check": r.format_check,
                "format_check_reason": r.format_check_reason,
                "discovery_check_reason": r.discovery_check_reason,
                "assist_check_reason": r.assist_check_reason,
                "assist": r.assist,
                "phrase_check": r.phrase_check,
                "phrase_check_reason": r.phrase_check_reason,
                "value_check": r.value_check,
                "value_check_reason": r.value_check_reason,
                "source_rule": r.source_rule,
                "authoritative_sources": list(r.authoritative_sources),
                "source_hits": list(r.source_hits),
                "expected_source_listed": r.expected_source_listed,
                "foreign_project_listed": r.foreign_project_listed,
                "foreign_projects": list(r.foreign_projects),
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
        f"`DEMO_TODAY`: {report.demo_today} · `EMBEDDINGS_ENABLED`: {report.embeddings_enabled}"
        f" · puanlayıcı v{SCORER_VERSION}",
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
    failed_safety = report.safety_failed
    if report.safety_evaluated:
        mark = "✅" if not failed_safety else "❌"
        lines.append(
            f"**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** {mark} "
            f"{report.safety_evaluated - len(failed_safety)}/{report.safety_evaluated}"
        )
        lines.append("")
    verdict = (
        "✅ tüm eşikler karşılandı"
        if report.ok
        else "❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü"
    )
    lines.append(f"**Genel sonuç:** {verdict}")
    evaluated = [r for r in report.results if r.error is None]
    fallbacks = report.router_fallbacks
    lines.append(
        f"**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** "
        f"{len(fallbacks)}/{len(evaluated)}"
        + (f" — {', '.join(r.id for r in fallbacks)}" if fallbacks else "")
    )
    # F0 A6: two separate observation lines (never part of the verdict).
    counters = report.discovery_summary
    for label, key in (("tüm sorular", "all"), ("discovery", "discovery")):
        block = counters[key]
        lines.append(
            f"**Keşif sayacı — beklenen belge gösterildi ({label}):** "
            f"{block['expected_source_listed']}/{block['expected_source_measurable']}"
        )
        lines.append(
            f"**Keşif sayacı — listede yabancı proje var ({label}):** "
            f"{block['foreign_project_listed']}/{block['foreign_project_measurable']}"
            + (
                f" — {', '.join(block['foreign_project_ids'])}"
                if block["foreign_project_ids"]
                else ""
            )
        )

    failed = [r for r in report.results if r.error is None and not r.passed]
    if failed:
        lines += ["", "## Başarısız sorular", ""]
        for r in failed:
            reasons = []
            if not r.answered_ok:
                reasons.append(f"answered={r.answered} bekleniyordu={not r.expect_no_answer}")
            if r.required_sources_missing and r.source_rule == "set":
                kume = list(r.authoritative_sources)
                reasons.append(f"gösterilen kaynak yetkili kümede değil (küme: {kume})")
            elif r.required_sources_missing:
                reasons.append(f"eksik kaynak: {list(r.required_sources_missing)}")
            if r.forbidden_sources_hit:
                reasons.append(f"yasak kaynak geldi: {list(r.forbidden_sources_hit)}")
            if r.phrase_check == "fail":
                reasons.append(f"ifade kontrolü: {r.phrase_check_reason}")
            if r.value_check == "fail":
                reasons.append("beklenen değer metinde bulunamadı")
            if r.safety_check == "fail":
                reasons.append("güvenlik: " + "; ".join(r.safety_reasons))
            if r.assist_check == "fail":
                reasons.append(f"assist: {r.assist_check_reason}")
            if r.discovery_check == "fail":
                reasons.append(f"discovery: {r.discovery_check_reason}")
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
    ea = question.expected_answer
    refs = [r.removeprefix("ledger:") for r in (ea if isinstance(ea, list) else [ea])]
    pages: set[Page] = set()
    for path, found in index.pages_by_path.items():
        if any(path == ref or path.startswith(ref + ".") for ref in refs):
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
    phrase_ok: bool | None = None  # None = no phrase rules on the question
    safety_ok: bool | None = None  # ADR-027 G1–G3; None = not evaluated
    assist_ok: bool | None = None  # ADR-027 expect_assist; None = not applicable
    safety_reasons: tuple[str, ...] = ()
    answer_text: str = ""
    assist: dict[str, Any] | None = None


@dataclass(frozen=True)
class ConsistencySummary:
    retrieval_stable: int  # questions whose target_in_prompt agrees across all repeats
    retrieval_measurable: int
    model_answered: int  # repeats with target_in_prompt=True that were answered
    model_measurable: int  # repeats with target_in_prompt=True
    value_ok: int
    value_measurable: int
    phrase_ok: int = 0
    phrase_measurable: int = 0


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
    phrased = [o for o in outcomes if o.error is None and o.phrase_ok is not None]
    return ConsistencySummary(
        retrieval_stable=retrieval_stable,
        retrieval_measurable=retrieval_measurable,
        model_answered=sum(1 for o in with_target if o.answered),
        model_measurable=len(with_target),
        value_ok=sum(1 for o in valued if o.value_ok),
        value_measurable=len(valued),
        phrase_ok=sum(1 for o in phrased if o.phrase_ok),
        phrase_measurable=len(phrased),
    )


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} (%{100.0 * num / den:.1f})" if den else "–"


def render_consistency_markdown(outcomes: list[RepeatOutcome], *, label: str) -> str:
    s = summarize_consistency(outcomes)
    safety_measurable = sum(1 for o in outcomes if o.safety_ok is not None)
    safety_ok = sum(1 for o in outcomes if o.safety_ok)
    assist_measurable = sum(1 for o in outcomes if o.assist_ok is not None)
    assist_ok = sum(1 for o in outcomes if o.assist_ok)
    lines = [
        f"# Tutarlılık ölçümü — {label}",
        "",
        f"- **Retrieval kararlılığı** (hedef sayfa her tekrarda aynı şekilde girdi/girmedi): "
        f"{_pct(s.retrieval_stable, s.retrieval_measurable)}",
        f"- **Model kararlılığı** (hedef sayfa prompt'tayken cevap verdi): "
        f"{_pct(s.model_answered, s.model_measurable)}",
        f"- **Uçtan uca** (beklenen değer cevapta): {_pct(s.value_ok, s.value_measurable)}",
        f"- **İfade kuralı** (zorunlu var, yasak yok — Ü-3): "
        f"{_pct(s.phrase_ok, s.phrase_measurable)}",
        "",
        f"- **Güvenlik G1–G3** (ADR-027, %100 zorunlu): {_pct(safety_ok, safety_measurable)}",
        f"- **Assist türü** (`expect_assist` eşleşti): {_pct(assist_ok, assist_measurable)}",
        "",
        "| Soru | Tekrar | Hedef prompt'ta | Cevapladı | Değer doğru | İfade | Güvenlik "
        "| Assist | Hata |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def mark(value: bool | None) -> str:
        return "–" if value is None else ("✅" if value else "❌")

    for o in outcomes:
        lines.append(
            f"| {o.id} | {o.repeat} | {mark(o.target_in_prompt)} | {mark(o.answered)} | "
            f"{mark(o.value_ok)} | {mark(o.phrase_ok)} | {mark(o.safety_ok)} | "
            f"{mark(o.assist_ok)} | {o.error or ''} |"
        )
    return "\n".join(lines) + "\n"
