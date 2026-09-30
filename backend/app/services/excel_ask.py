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
from app.excel.sql_guard import SqlRejectedError
from app.models.document import Document
from app.models.user import User
from app.repositories import document_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.excel import ExcelAskRequest, ExcelSourceCard
from app.services.audit_writer import write_audit_row
from app.services.authorization import allowed_document_ids
from app.services.llm import LLMClient, LLMRequest

log = logging.getLogger(__name__)

QUERY_TYPE = "DATA_QUERY"
PlanKind = Literal["function", "sql", "none"]

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
    "quarters as Q2_2026, months as 2026-06, years as 2026."
)

ANSWER_SYSTEM_PROMPT = (
    "Sen bir şirket bilgi asistanısın. Sana bir soru ve DuckDB/Python tarafından hesaplanmış "
    "sonuç verilecek. Türkçe, bir ya da iki kısa cümleyle sonucu aktar. KURALLAR: 1. Sonuçtaki "
    "rakamı AYNEN verilen biçimde yaz, yeniden hesaplama, yuvarlama, birim değiştirme. 2. Yorum, "
    "tahmin, öneri, projeksiyon yazma. 3. Kaynak etiketi ekleme; kaynak ayrıca gösterilecek."
)


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


# ---------------------------------------------------------------- formatting


def format_value(value: Any, unit: str | None) -> str:
    """TR conventions (CLAUDE.md): thousands with `.`, decimals with `,`; `1,37x`,
    `44.100.000 EUR`, `%38,2`, `108.858 MWh`."""
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


def _value_variants(value: Any, unit: str | None) -> set[str]:
    tr = format_value(value, unit)
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


def _sql_value(result: QueryResult) -> tuple[Any, str]:
    """A 1×1 result is *the* number; anything else is relayed as a compact table."""
    if len(result.rows) == 1 and len(result.columns) == 1:
        return result.rows[0][0], ""
    header = " | ".join(result.columns)
    body = "\n".join(" | ".join(str(v) for v in row) for row in result.rows[:20])
    return None, f"{header}\n{body}"


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
) -> ExcelAskResult:
    """`write_audit=False` (Phase 4.3): the router owns the call's single audit row."""
    started = time.perf_counter()
    scope = AuthorizationScope(department=request.department)
    allowed = allowed_document_ids(user, scope, SqlDocumentIdsProvider(session))
    if request.document_ids:
        allowed = allowed & set(request.document_ids)
    documents = document_repo.list_excel_by_ids(session, allowed)
    workbooks, needs_recalc = _load_workbooks(documents, engine, settings.documents_dir)

    def finish(result: ExcelAskResult, *, error: str | None = None) -> ExcelAskResult:
        if write_audit:
            _write_audit(session, user, request, result, started, error)
        return result

    if not workbooks:
        text = RECALC_TEXT if needs_recalc else NO_DATA_TEXT
        return finish(
            ExcelAskResult(answer=text, answered=False, value=None, unit=None, formatted_value=None)
        )

    plan_response = llm.complete(
        LLMRequest(
            system=PLAN_SYSTEM_PROMPT,
            user=f"{_catalogue(workbooks)}\n\nQUESTION: {request.question}",
            model=settings.llm_model_classify,
            max_output_tokens=400,
            response_format="json_object",
        )
    )
    plan = _parse_plan(plan_response.text)
    tokens_in, tokens_out = plan_response.tokens_in, plan_response.tokens_out
    loaded = [wb for _, wb in workbooks]

    calc: CalcResult | None = None
    query: QueryResult | None = None
    try:
        if plan["kind"] == "function":
            calc = run_function(
                engine, loaded, str(plan.get("name")), dict(plan.get("params") or {})
            )
        elif plan["kind"] == "sql":
            query = engine.run_sql(loaded, str(plan.get("sql") or ""))
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
                model=plan_response.model,
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
                model=plan_response.model,
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
                model=plan_response.model,
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
                model=plan_response.model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
        )

    if calc is not None:
        value, unit, detail = calc.value, calc.unit, calc.detail
        sources = [_card(calc.source)]
        table_text = ""
    else:
        assert query is not None
        value, table_text = _sql_value(query)
        unit, detail = "", "SQL"
        sources = [_card(s) for s in query.sources]
    formatted = format_value(value, unit) if value is not None else None

    result_block = (
        f"SORU: {request.question}\nSONUÇ: {formatted if formatted else table_text}\n"
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
    if value is not None and not any(v in answer for v in _value_variants(value, unit)):
        log.warning("excel answer dropped engine value, using template", extra={"answer": answer})
        answer = f"Sonuç: {formatted} ({detail})."
    if value is None and not answer:
        answer = table_text
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
