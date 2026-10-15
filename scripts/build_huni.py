"""İş Emri 2026-10-15A2 §0 — the funnel table: every remaining loss of a re-scored run is
assigned to exactly one stage, with LLM-free evidence for stages 1–2 taken from the run's
own audit rows (`chunks_retrieved` → was the target page in the prompt? what was the project
distribution of the retrieved documents?) plus the scorer's failure reasons.

Stages: 1 Arama · 2 Proje ekseni · 2b Router · 3a Israrlı red · 3b Kural · 4 Excel ·
5 Puanlama-kaynak. Runs inside the eval backend container (page texts and document→project
come from that DB; no LLM):

    python -m scripts.build_huni --rescored results/s3_rescored --audit logs/s3_audit.jsonl \
        --out results/huni/s3_rescored_huni.md
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.db import get_session_factory
from app.models.document import Document
from app.models.project import Project
from app.services.assist import named_project_codes
from scripts import eval_lib
from scripts.rescore import load_audit_rows
from scripts.run_eval import _Targets

STAGES = {
    "1": "1 Arama",
    "2": "2 Proje ekseni",
    "2b": "2b Router",
    "3a": "3a Israrlı red",
    "3b": "3b Kural",
    "4": "4 Excel",
    "5": "5 Puanlama-kaynak",
}

# Assignments the evidence columns cannot decide alone (S3 raporu §3.4 okumasıyla): the
# answer carries the right fact in a spelling the scorer's patterns miss (5), the workbook
# can never be reached through chunk retrieval (1), the router sent a document question to
# Excel (2b), the model omitted the fact although the page was in the prompt (3a), a rule
# was broken on an otherwise correct answer (3b).
OVERRIDES: dict[str, tuple[str, str]] = {
    "ANK-FIN-004": ("5", "değer doğru, «ECA katılımı olmadığı» kalıp dışı"),
    "ANK-NEG-002": ("5", "değer doğru, «ECA katılımı görünmüyor» kalıp dışı"),
    "ANK-FIN-013": ("5", "değerler doğru, `3.25%` yazımı (F-8/kalıp)"),
    "IZM-DEV-007": ("5", "adımlar doğru, ÇED yazısı yetkili kümede değil (ledger taşıyıcı yok)"),
    "ANK-OPS-003": ("2b", "router DATA → workbook; adıyla sorulan Aralık 2023 raporu belge"),
    "GEN-DSC-008": ("1", "xlsx (Budget vs Actual) parça taşımaz, keşfe giremez"),
    "GEN-DSC-008-M": ("1", "router DATA → plan none → belge düşüşü; xlsx keşfe giremez"),
    "GEN-GEN-003": ("3b", "genel bilgi sorusu cevaplandı (GEN-001/002 reddedildi)"),
    "GEN-CMP-003": ("3b", "değerler doğru, karşılaştırma sabit cümlesi yok"),
    "ANK-OPS-001": ("3a", "Ağustos 2026 raporu promptta, «3. işletme yılı» aktarılmadı"),
    "GEN-DSC-011": ("4", "MIXED: Excel tek hücre (tutar), tarih düştü; FA belgesi gösterilmedi"),
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build_huni")
    parser.add_argument("--rescored", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--questions", type=Path, default=eval_lib.DEFAULT_QUESTIONS)
    parser.add_argument("--master", type=Path, default=eval_lib.DEFAULT_MASTER)
    parser.add_argument("--manifest", type=Path, default=eval_lib.DEFAULT_MANIFEST)
    return parser


def _project_by_document(session: Any) -> dict[str, str | None]:
    codes = {p.id: p.code for p in session.scalars(select(Project)).all()}
    rows = session.execute(select(Document.id, Document.project_id)).all()
    return {str(d): codes.get(p) for d, p in rows}


def _title_by_document(session: Any) -> dict[str, str]:
    return {str(d): t for d, t in session.execute(select(Document.id, Document.title)).all()}


def assign(
    *,
    qid: str,
    result: dict[str, Any],
    target_in_prompt: bool | None,
    expected_retrieved: bool | None,
    named: set[str],
    assist: dict[str, Any] | None,
    foreign_listed: bool | None,
) -> tuple[str, str]:
    if qid in OVERRIDES:
        return OVERRIDES[qid]
    kind = (assist or {}).get("kind")
    g3 = any("G3" in r for r in result.get("safety_reasons") or [])
    if foreign_listed or g3 or result.get("forbidden_sources_hit"):
        return "2", "listede/cevapta yabancı proje"
    if not result["answered"] and kind == "disambiguate" and not named:
        return "2", "proje adı yok → eksen disambiguate, liste yok"
    if (
        not result["answered"]
        and kind == "clarify"
        and not named
        and (target_in_prompt or expected_retrieved)
    ):
        return "2", "proje adı yok → eksen netleştirmesi, belge erişimde"
    if target_in_prompt is False or expected_retrieved is False:
        return "1", "hedef sayfa/beklenen belge top-80'de değil"
    if not result["answered"] and (target_in_prompt or expected_retrieved):
        return "3a", "beklenen belge promptta, cevap yok"
    return "5", "sınıflandırılamadı — elle bak"


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    rescored = json.loads((args.rescored / "results.json").read_text(encoding="utf-8"))
    audit_rows = load_audit_rows(args.audit)  # run order == results order (rescore.align)
    question_set = eval_lib.load_questions(args.questions)
    questions = {q.id: q for q in question_set.questions}
    raws = eval_lib.load_ledger_raws(args.master)
    targets = _Targets(args, raws)
    catalog = eval_lib.build_document_catalog(args.manifest)

    lines = [
        "# Huni tablosu — S3 yeniden puanlama (v2.0) kalan kayıplar",
        "",
        "Her kayıp tek aşamaya atanır. Aşama 1–2 kanıtı LLM'siz: S3 audit `chunks_retrieved` "
        "(hedef sayfa top-80'de mi?) + getirilen belgelerin proje dağılımı; `assist.kind`/`axis` "
        "S3 cevabından; diğerleri `OVERRIDES` (S3 raporu §3.4 okuması, betikte gerekçeli).",
        "",
        "| Soru | Kat. | Aşama | Hedef sayfa top-80 | Beklenen belge top-80 | "
        "Proje dağılımı (getirilen) | Adlı | assist | Yabancı listede | Puanlayıcı sebebi | Not |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    counts: Counter[str] = Counter()
    with get_session_factory()() as session:
        project_of = _project_by_document(session)
        title_of = _title_by_document(session)
        for result, audit in zip(rescored["questions"], audit_rows, strict=True):
            if result["question"] != audit["question"]:
                raise SystemExit(f"{result['id']}: results and audit rows out of order")
            if result["passed"]:
                continue
            qid = result["id"]
            question = questions[qid]
            retrieved = {
                (title_of.get(c["document_id"], "?"), int(c["page_number"]))
                for c in audit["chunks_retrieved"]
            }
            target = targets.for_question(question)
            target_in_prompt = bool(retrieved & target) if target else None
            docs = list(dict.fromkeys(c["document_id"] for c in audit["chunks_retrieved"]))
            dist = Counter(project_of.get(d) for d in docs)
            retrieved_titles = frozenset(title_of.get(d, "?") for d in docs)
            expected_retrieved: bool | None = None
            if question.required_sources:
                expected_retrieved = any(
                    eval_lib._source_satisfied(n, retrieved_titles, catalog)
                    for n in question.required_sources
                )
            named = named_project_codes(session, question.question)
            assist = result.get("assist")
            stage, note = assign(
                qid=qid,
                result=result,
                target_in_prompt=target_in_prompt,
                expected_retrieved=expected_retrieved,
                named=named,
                assist=assist,
                foreign_listed=result.get("foreign_project_listed"),
            )
            counts[stage] += 1
            reasons = _reasons(result)
            dist_text = ", ".join(
                f"{code or 'grup'}:{n}" for code, n in sorted(dist.items(), key=lambda kv: -kv[1])
            )
            tip = "—" if target_in_prompt is None else ("✅" if target_in_prompt else "❌")
            erp = "—" if expected_retrieved is None else ("✅" if expected_retrieved else "❌")
            kind = (assist or {}).get("kind") or "—"
            axis = (assist or {}).get("axis")
            kind_text = f"{kind}/{axis}" if axis else kind
            foreign = result.get("foreign_project_listed")
            foreign_text = "—" if foreign is None else ("✅" if foreign else "❌")
            lines.append(
                f"| {qid} | {result['category']} | **{STAGES[stage]}** | {tip} | {erp} | "
                f"{dist_text} | {','.join(sorted(named)) or '—'} | {kind_text} | {foreign_text} | "
                f"{reasons} | {note} |"
            )
    lines += ["", "## Özet — aşama başına kayıp", "", "| Aşama | Sayı |", "|---|---|"]
    for key in STAGES:
        lines.append(f"| {STAGES[key]} | {counts.get(key, 0)} |")
    lines.append(f"| **Toplam** | **{sum(counts.values())}** |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def _reasons(result: dict[str, Any]) -> str:
    parts = []
    if not result["answered_ok"]:
        parts.append(f"answered={result['answered']}")
    if result.get("required_sources_missing"):
        parts.append("kaynak")
    if result.get("forbidden_sources_hit"):
        parts.append("yasak kaynak")
    if result.get("value_check") == "fail":
        parts.append("değer")
    if result.get("phrase_check") == "fail":
        parts.append("ifade")
    if result.get("safety_check") == "fail":
        parts.append(
            "G: "
            + "; ".join(
                r.split(":")[0] + ":" + r.split(":")[1][:40] for r in result["safety_reasons"]
            )
        )
    if result.get("discovery_check") == "fail":
        parts.append("discovery")
    return "; ".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
