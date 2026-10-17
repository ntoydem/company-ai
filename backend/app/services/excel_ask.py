"""`POST /api/excel/ask` pipeline (SPEC_04 §3-5, ADR-011): authorize → catalogue of the
workbooks the user may see → planning LLM picks a predefined function or one read-only
SELECT (JSON) → the engine computes → answering LLM phrases the result in Turkish → the
number in the answer is checked against the engine's value (else a template answer) →
audit row. The final figure never comes from a model."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.excel.calc import (
    CalcResult,
    CalculationEngine,
    ExcelError,
    LoadedWorkbook,
    NeedsRecalculationError,
    QueryResult,
    SourceRange,
)
from app.excel.functions import FUNCTIONS, FunctionError, run_function
from app.excel.future_guard import FutureRow, future_row
from app.excel.sql_guard import SqlRejectedError
from app.models.document import Document
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.excel import ExcelAskRequest, ExcelSourceCard
from app.services import tr_format
from app.services.answer_prompt import NO_ANSWER_TEXT
from app.services.audit_writer import write_audit_row
from app.services.authorization import allowed_document_ids
from app.services.excel_scope import answer_project, project_question, scope_workbooks
from app.services.llm import LLMClient, LLMRequest
from app.services.temporal import today as temporal_today

log = logging.getLogger(__name__)

QUERY_TYPE = "DATA_QUERY"
PlanKind = Literal["function", "sql", "none"]

# İş Emri 2026-10-13S0a (K-B1 §4a / J §3a): a `kind=sql` plan whose result is not exactly
# one cell gets ONE more planning call with feedback; a second non-scalar result ends in
# the fixed no-answer sentence. The table never reaches the answering model (ADR-011).
PLAN_MAX_ATTEMPTS = 2
_CANDIDATE_LABEL_LIMIT = 20

NO_DATA_TEXT = "Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım."
RECALC_TEXT = (
    "Dosyanın Excel'de yeniden hesaplanıp kaydedilmesi gerekiyor (formül sonuçları dosyada yok)."
)
SQL_REJECTED_TEXT = "Bu veri sorgusu güvenlik kuralına takıldı."
TIMEOUT_TEXT = "Sorgu zaman aşımına uğradı."

PLAN_SYSTEM_PROMPT = (
    "You plan how to answer a data question about Excel workbooks. You never compute numbers "
    "yourself. Reply with ONE JSON object and nothing else, in one of these shapes:\n"
    '{"kind":"function","name":"<function>","params":{...}}\n'
    '{"kind":"sql","sql":"SELECT ... FROM <table> ..."}\n'
    '{"kind":"none","reason":"<why the catalogue cannot answer>"}\n'
    "Rules: prefer a predefined function when one fits; otherwise write a single read-only "
    "SELECT over the listed tables only (no semicolons, no comments, no other statements, "
    "no file functions). Use the exact table and column names from the catalogue. Periods: "
    "quarters as Q2_2026, months as 2026-06, years as 2026. TODAY in the context is the "
    "system's current date: resolve relative expressions (last month, this quarter, next "
    "instalment) against it and ask for exactly that period — never substitute an earlier "
    "period because the asked one might be missing; the engine reports missing data itself. "
    "'Latest' or 'most recent' means the newest row in the data that is not after TODAY, not "
    "a period you guess. Rows dated after TODAY are projections, not current values: when "
    "the question asks for the current, present, still-outstanding or remaining value "
    "(güncel, şu an, hâlâ, kalan, en son dönem), take the newest row whose date column "
    "(end_date, period end, month) is on or before TODAY — filter it first (e.g. WHERE "
    "end_date <= DATE 'TODAY') and only then ORDER BY ... DESC LIMIT 1. Select a row after "
    "TODAY only when the question explicitly names a future period or date (in 2030, ne "
    'olacak, projection), and then add "future_ok": true to the JSON.'
)

ANSWER_SYSTEM_PROMPT = (
    "Sen bir şirket bilgi asistanısın. Sana bir soru ve DuckDB/Python tarafından hesaplanmış "
    "sonuç verilecek. Türkçe, bir ya da iki kısa cümleyle sonucu aktar. KURALLAR: 1. Sonuçtaki "
    "rakamı AYNEN verilen biçimde yaz, yeniden hesaplama, yuvarlama, birim değiştirme. 2. Yorum, "
    "tahmin, öneri, projeksiyon yazma. 3. Kaynak etiketi ekleme; kaynak ayrıca gösterilecek."
)


@dataclass(frozen=True)
class AmbiguousResult:
    """S0-a: both SQL attempts returned a table instead of one value. The hook for the B2
    clarifying question — row labels only (first string cell per row), never a number.
    Not shown to the user in this round."""

    rows: int
    columns: tuple[str, ...]
    candidates: tuple[str, ...]
    attempts: int


@dataclass(frozen=True)
class ExcelAskResult:
    answer: str
    answered: bool
    value: Any
    unit: str | None
    formatted_value: str | None
    sources: list[ExcelSourceCard] = field(default_factory=list)
    plan_kind: PlanKind = "none"
    plan: dict[str, Any] = field(default_factory=dict)
    excel_files: list[str] = field(default_factory=list)
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    # S0-a: set only when the engine guard ended the call (answered=False); `sources` then
    # lists the ranges that were *tried*, not a source of an answer.
    ambiguous: AmbiguousResult | None = None
    # ADR-036: no project named and the data is held by several projects (or two projects
    # named) — `answer` is this one question, no figure was shown to anyone (answered=False).
    project_question: str | None = None


# ---------------------------------------------------------------- formatting


def format_value(value: Any, unit: str | None, *, ek_f: bool = False) -> str:
    """TR conventions (CLAUDE.md): thousands with `.`, decimals with `,`; `1,37x`,
    `44.100.000 EUR`, `%38,2`, `108.858 MWh`. With `ek_f` (ADR-030 F-8) the shared
    `tr_format` rules apply instead (currency codes, ≥ 2 percent decimals, no rounding);
    without it this is the Phase 4.2 formatter, byte for byte."""
    if ek_f:
        return tr_format.format_value(value, unit)
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    number = float(value)
    if unit == "x":
        return f"{number:.2f}x".replace(".", ",")
    if unit == "%":
        return "%" + f"{number:.1f}".replace(".", ",")
    if number.is_integer():
        text = f"{int(number):,}".replace(",", ".")
    else:
        text = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} {unit}".strip() if unit else text


def _value_variants(value: Any, unit: str | None, *, ek_f: bool = False) -> set[str]:
    tr = format_value(value, unit, ek_f=ek_f)
    variants = {tr}
    if isinstance(value, int | float):
        number = float(value)
        if unit == "x":
            variants.add(f"{number:.2f}x")
        elif unit == "%":
            variants.add(f"{number:.1f}%")
            variants.add(f"%{number:.1f}")
        elif number.is_integer():
            variants.add(f"{int(number):,}")
            variants.add(str(int(number)))
        else:
            variants.add(f"{number:,.2f}")
    return variants


# ---------------------------------------------------------------- catalogue / plan


def _catalogue(workbooks: list[tuple[Document, LoadedWorkbook]]) -> str:
    lines = ["WORKBOOKS:"]
    for document, wb in workbooks:
        lines.append(f"- file: {wb.file} (title: {document.title}, type: {document.document_type})")
        for table, sheet in wb.sheet_by_table.items():
            columns = [c for c in wb.tables[table].columns]
            lines.append(f"  table {table} (sheet {sheet!r}): columns {columns}")
        named = [n.name for n in wb.info.named_ranges]
        if named:
            lines.append(f"  named ranges: {named}")
    lines.append("FUNCTIONS:")
    for spec in FUNCTIONS.values():
        lines.append(f"- {spec.name}({', '.join(spec.params)}): {spec.description}")
    return "\n".join(lines)


def _parse_plan(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    try:
        plan = json.loads(text)
    except json.JSONDecodeError:
        return {"kind": "none", "reason": "unparseable plan"}
    if not isinstance(plan, dict) or plan.get("kind") not in {"function", "sql", "none"}:
        return {"kind": "none", "reason": "invalid plan"}
    return plan


def _kind(plan: dict[str, Any]) -> PlanKind:
    return cast(PlanKind, plan["kind"])


def plan_model(settings: Settings) -> str:
    """S0-a (11. tur §A3): the planning call may run on its own model
    (`LLM_MODEL_EXCEL_PLAN`); empty → the classify model, as before."""
    return settings.llm_model_excel_plan or settings.llm_model_classify


def _is_scalar(query: QueryResult) -> bool:
    return len(query.rows) == 1 and len(query.columns) == 1


def _is_number_like(value: str) -> bool:
    try:
        float(value.replace(".", "").replace(",", "."))
    except ValueError:
        return False
    return True


def candidate_labels(query: QueryResult) -> tuple[str, ...]:
    """Row labels for the retry feedback and the B2 hook: the first *string* cell of each
    row that does not read as a number — never a figure from the workbook."""
    labels: list[str] = []
    for row in query.rows:
        for cell in row:
            if isinstance(cell, str) and cell.strip() and not _is_number_like(cell):
                if cell not in labels:
                    labels.append(cell)
                break
        if len(labels) >= _CANDIDATE_LABEL_LIMIT:
            break
    return tuple(labels)


def retry_feedback(plan: dict[str, Any], query: QueryResult) -> str:
    """The one sentence the planning model gets on the second attempt (order text) — row
    count, column count, column names and candidate row labels; no cell values."""
    labels = candidate_labels(query)
    text = (
        f"ÖNCEKİ PLAN: {plan.get('sql', '')}\n"
        f"GERİ BİLDİRİM: sorgu {len(query.rows)} satır × {len(query.columns)} sütun döndürdü; "
        f"tek değer gerekiyor; sütunlar: {list(query.columns)}."
    )
    if labels:
        text += f" Aday satır başlıkları: {list(labels)}."
    return text + " Tek hücre (1 satır × 1 sütun) döndüren yeni bir plan yaz."


def future_feedback(plan: dict[str, Any], row: FutureRow, today: date) -> str:
    """S2c: the one sentence for the re-plan after a row dated after TODAY — table, date
    column and row *label* (no cell value, no date of the row), plus the two ways out:
    filter to `<= TODAY`, or declare the future period with `future_ok`."""
    where = f"tablo {row.table}, sütun {row.date_column}"
    if row.label:
        where += f", satır başlığı {row.label!r}"
    return (
        f"ÖNCEKİ PLAN: {plan.get('sql', '')}\n"
        f"GERİ BİLDİRİM: seçilen satır bugünden sonra ({where}); güncel değer isteniyor. "
        f"Tarihi TODAY'e ({today.isoformat()}) eşit ya da ondan önceki son satırı seçen yeni bir "
        f"plan yaz (örn. WHERE {row.date_column} <= DATE '{today.isoformat()}' ORDER BY "
        f"{row.date_column} DESC LIMIT 1). Soru açıkça gelecek bir dönemi istiyorsa aynı planı "
        '"future_ok": true alanıyla yaz.'
    )


def _load_workbooks(
    documents: list[Document], engine: CalculationEngine, documents_dir: Path
) -> tuple[list[tuple[Document, LoadedWorkbook]], list[str]]:
    loaded: list[tuple[Document, LoadedWorkbook]] = []
    needs_recalc: list[str] = []
    for document in documents:
        path = documents_dir / document.storage_path
        try:
            loaded.append(
                (document, engine.load(path, document_id=document.id, file_name=document.file_name))
            )
        except NeedsRecalculationError:
            needs_recalc.append(document.title)
        except ExcelError as exc:
            log.warning(
                "workbook skipped", extra={"document_id": str(document.id), "error": str(exc)}
            )
    return loaded, needs_recalc


def _card(source: SourceRange) -> ExcelSourceCard:
    return ExcelSourceCard(
        document_id=source.document_id,
        file=source.file,
        sheet=source.sheet,
        range=source.ref,
        label=source.label,
    )


def _sql_value(result: QueryResult, *, ek_f: bool = False) -> tuple[Any, str, str]:
    """A 1×1 result is *the* number; anything else is rendered as a compact table. With `ek_f`
    (ADR-030 F-8) the 1×1 unit is read from the column label (`"Debt (EUR)"` → `EUR`) and the
    table cells are formatted by code (`72.000.000 EUR`, `15.11.2021`). Since S0-a the
    pipeline calls this for 1×1 results only (the engine guard stops a table before any
    model sees it); the table branch stays for `tr_format`'s own tests."""
    if len(result.rows) == 1 and len(result.columns) == 1:
        value = result.rows[0][0]
        if not ek_f:
            return value, "", ""
        if isinstance(value, datetime | date):
            return tr_format.format_date(value), "", ""
        return value, tr_format.unit_from_label(result.columns[0]) or "", ""
    header = " | ".join(result.columns)
    if not ek_f:
        body = "\n".join(" | ".join(str(v) for v in row) for row in result.rows[:20])
        return None, "", f"{header}\n{body}"
    body = "\n".join(
        " | ".join(
            tr_format.format_cell(v, label) for v, label in zip(row, result.columns, strict=False)
        )
        for row in result.rows[:20]
    )
    return None, "", f"{header}\n{body}"


# ---------------------------------------------------------------- pipeline


def answer_data_question(
    session: Session,
    user: User,
    request: ExcelAskRequest,
    llm: LLMClient,
    settings: Settings,
    engine: CalculationEngine,
    *,
    write_audit: bool = True,
    original_question: str | None = None,
) -> ExcelAskResult:
    """`write_audit=False` (Phase 4.3): the router owns the call's single audit row.
    `original_question` (ADR-036): the user's own wording when `request.question` is the
    router's sub-question — project names are read from what the user typed."""
    started = time.perf_counter()
    allowed = allowed_document_ids(
        user, AuthorizationScope(department=request.department), SqlDocumentIdsProvider(session)
    )
    if request.document_ids:
        allowed = allowed & set(request.document_ids)
    # ADR-036: narrowed inside `allowed` — a workbook outside it never reaches the catalogue.
    scope = scope_workbooks(session, allowed, original_question or request.question)
    workbooks, needs_recalc = _load_workbooks(scope.documents, engine, settings.documents_dir)
    catalogue_documents = [document for document, _ in workbooks]

    def finish(result: ExcelAskResult, *, error: str | None = None) -> ExcelAskResult:
        if write_audit:
            _write_audit(session, user, request, result, started, error)
        return result

    if not workbooks:
        text = RECALC_TEXT if needs_recalc else NO_DATA_TEXT
        return finish(
            ExcelAskResult(answer=text, answered=False, value=None, unit=None, formatted_value=None)
        )

    catalogue = _catalogue(workbooks)
    loaded = [wb for _, wb in workbooks]
    # S0-b (Tansu §0/2-1): the planner sees the system's own date (ADR-026) so "last
    # month" resolves to a period, not to a guess; the same date feeds the functions.
    today_ = temporal_today(settings)
    tokens_in = tokens_out = 0
    plan_model_name: str | None = None

    def request_plan(feedback: str | None) -> dict[str, Any]:
        nonlocal tokens_in, tokens_out, plan_model_name
        user = f"{catalogue}\n\nTODAY: {today_.isoformat()}\nQUESTION: {request.question}"
        if feedback:
            user += f"\n\n{feedback}"
        response = llm.complete(
            LLMRequest(
                system=PLAN_SYSTEM_PROMPT,
                user=user,
                model=plan_model(settings),
                max_output_tokens=400,
                response_format="json_object",
            )
        )
        tokens_in += response.tokens_in
        tokens_out += response.tokens_out
        plan_model_name = response.model
        return _parse_plan(response.text)

    def asked_project(read_from: list[SourceRange], plan: dict[str, Any]) -> ExcelAskResult | None:
        """ADR-036: before any figure or the answering model — which project?"""
        used = [s.document_id for s in read_from if s.document_id is not None]
        question = project_question(session, scope, used, catalogue_documents)
        if question is None:
            return None
        log.info("excel project question", extra={"plan": plan, "question": question})
        return ExcelAskResult(
            question,
            False,
            None,
            None,
            None,
            plan_kind=_kind(plan),
            plan=plan,
            model=plan_model_name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            project_question=question,
        )

    def execute(plan: dict[str, Any]) -> tuple[CalcResult | None, QueryResult | None]:
        if plan["kind"] == "function":
            return (
                run_function(
                    engine,
                    loaded,
                    str(plan.get("name")),
                    dict(plan.get("params") or {}),
                    today=today_,
                ),
                None,
            )
        if plan["kind"] == "sql":
            return None, engine.run_sql(loaded, str(plan.get("sql") or ""))
        return None, None

    plan = request_plan(None)
    calc: CalcResult | None = None
    query: QueryResult | None = None
    tried: list[SourceRange] = []
    try:
        for attempt in range(1, PLAN_MAX_ATTEMPTS + 1):
            calc, query = execute(plan)
            if query is None:
                break
            future: FutureRow | None = None
            if _is_scalar(query):
                # S2c guard (B2-b §4c): one value read from a row dated after TODAY is a
                # projection; without `future_ok` in the plan it is not the current value.
                if plan.get("future_ok") is True:
                    break
                future = future_row(loaded, str(plan.get("sql") or ""), query.rows[0][0], today_)
                if future is None:
                    break
                log.info(
                    "excel sql result after today",
                    extra={
                        "attempt": attempt,
                        "table": future.table,
                        "date_column": future.date_column,
                        "excel_row": future.excel_row,
                        "sql": plan.get("sql"),
                    },
                )
            else:
                # Engine guard (ADR-011): a table is not a result. Log the SQL (J §3a: it
                # was recorded nowhere) and either re-plan once or stop.
                log.info(
                    "excel sql result not scalar",
                    extra={
                        "attempt": attempt,
                        "rows": len(query.rows),
                        "columns": list(query.columns),
                        "sql": plan.get("sql"),
                    },
                )
            tried += [s for s in query.sources if s not in tried]
            if attempt == PLAN_MAX_ATTEMPTS:
                asked = asked_project(tried, plan)
                if asked is not None:
                    return finish(asked)
                return finish(
                    ExcelAskResult(
                        NO_ANSWER_TEXT,
                        False,
                        None,
                        None,
                        None,
                        sources=[_card(s) for s in tried],
                        plan_kind="sql",
                        plan=plan,
                        excel_files=sorted({s.file for s in tried}),
                        model=plan_model_name,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        ambiguous=None
                        if future is not None
                        else AmbiguousResult(
                            rows=len(query.rows),
                            columns=tuple(query.columns),
                            candidates=candidate_labels(query),
                            attempts=attempt,
                        ),
                    )
                )
            feedback = (
                future_feedback(plan, future, today_)
                if future is not None
                else retry_feedback(plan, query)
            )
            plan = request_plan(feedback)
            calc = query = None
    except FunctionError as exc:
        log.info("excel function failed", extra={"plan": plan, "error": str(exc)})
        return finish(
            ExcelAskResult(
                NO_DATA_TEXT,
                False,
                None,
                None,
                None,
                plan_kind=_kind(plan),
                plan=plan,
                model=plan_model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            ),
            error=None,
        )
    except SqlRejectedError as exc:
        log.warning("excel sql rejected", extra={"plan": plan, "reason": exc.reason})
        return finish(
            ExcelAskResult(
                SQL_REJECTED_TEXT,
                False,
                None,
                None,
                None,
                plan_kind="sql",
                plan=plan,
                model=plan_model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            ),
            error=f"sql rejected: {exc.reason}",
        )
    except ExcelError as exc:
        text = TIMEOUT_TEXT if exc.__class__.__name__ == "QueryTimeoutError" else NO_DATA_TEXT
        return finish(
            ExcelAskResult(
                text,
                False,
                None,
                None,
                None,
                plan_kind=_kind(plan),
                plan=plan,
                model=plan_model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            ),
            error=str(exc),
        )

    if calc is None and query is None:
        return finish(
            ExcelAskResult(
                NO_DATA_TEXT,
                False,
                None,
                None,
                None,
                plan_kind="none",
                plan=plan,
                model=plan_model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
        )

    read_from = [calc.source] if calc is not None else list(query.sources if query else [])
    asked = asked_project(read_from, plan)
    if asked is not None:
        return finish(asked)

    if calc is not None:
        value, unit, detail = calc.value, calc.unit, calc.detail
        sources = [_card(calc.source)]
    else:
        assert query is not None and _is_scalar(query)  # the guard above let only 1×1 through
        value, unit, _ = _sql_value(query, ek_f=settings.ek_f_enabled)
        detail = "SQL"
        sources = [_card(s) for s in query.sources]
    formatted = format_value(value, unit, ek_f=settings.ek_f_enabled) if value is not None else None

    result_block = (
        f"SORU: {request.question}\nSONUÇ: {formatted}\n"
        f"AÇIKLAMA: {detail}\nKAYNAK: {', '.join(s.label for s in sources)}"
    )
    answer_response = llm.complete(
        LLMRequest(
            system=ANSWER_SYSTEM_PROMPT,
            user=result_block,
            model=settings.llm_model_answer,
            max_output_tokens=settings.llm_max_output_tokens,
            reasoning_effort=settings.llm_reasoning_effort,
        )
    )
    tokens_in += answer_response.tokens_in
    tokens_out += answer_response.tokens_out
    answer = answer_response.text.strip()
    # ADR-011: the final figure never comes from the model — if the phrased answer does not
    # carry the engine's number verbatim, the template wins.
    if value is not None and not any(
        v in answer for v in _value_variants(value, unit, ek_f=settings.ek_f_enabled)
    ):
        log.warning("excel answer dropped engine value, using template", extra={"answer": answer})
        answer = f"Sonuç: {formatted} ({detail})."
    # ADR-036 (Tansu 17.10 madde 9): an unnamed question answered from one project's
    # workbook says which project — by code, next to the source card.
    read_ids = [s.document_id for s in read_from if s.document_id is not None]
    project = answer_project(session, scope, read_ids, catalogue_documents)
    if project is not None and project not in answer:
        answer = f"{project}: {answer}"
    return finish(
        ExcelAskResult(
            answer=answer,
            answered=True,
            value=value,
            unit=unit or None,
            formatted_value=formatted,
            sources=sources,
            plan_kind=_kind(plan),
            plan=plan,
            excel_files=sorted({s.file for s in sources}),
            model=answer_response.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
    )


def _write_audit(
    session: Session,
    user: User,
    request: ExcelAskRequest,
    result: ExcelAskResult,
    started: float,
    error: str | None,
) -> None:
    write_audit_row(
        session,
        user,
        question=request.question,
        query_type=QUERY_TYPE,
        scope_department=request.department,
        scope_project=None,
        documents_retrieved=excel_document_ids(result.sources),
        chunks=[],
        answer=result.answer,
        sources=[],
        excel_sources=result.sources,
        model=result.model,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        execution_ms=round((time.perf_counter() - started) * 1000),
        error=error,
    )


def excel_document_ids(sources: list[ExcelSourceCard]) -> list[UUID]:
    return list(dict.fromkeys(s.document_id for s in sources if s.document_id is not None))


def workbook_document_ids(session: Session, user: User) -> list[UUID]:
    allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider(session))
    return [d.id for d in document_repo.list_excel_by_ids(session, allowed)]
