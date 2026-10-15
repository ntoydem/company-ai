"""`scripts.rescore` (İş Emri 2026-10-15F0 E) — LLM-free re-scoring of a finished run: the
results/audit join, outcome reconstruction, rule attribution and an end-to-end `--no-db` run
over a one-question fixture (real questions.json/manifest/ledger, no server)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import rescore
from scripts.eval_lib import QuestionResult

_Q = "Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?"


def _old_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": "ANK-NEG-003",
        "category": "document",
        "ask_as_user": "finans",
        "question": "Kredi sözleşmesinin vadesi kaç yıl?",
        "expect_no_answer": True,
        "answered": False,
        "answer_text": _Q,
        "cited_titles": [],
        "query_type": "DOCUMENT_QUERY",
        "router_fallback": False,
        "answered_ok": True,
        "required_sources_missing": [],
        "forbidden_sources_hit": [],
        "safety_check": "fail",
        "safety_reasons": ["G2: cevapsız yanıt sabit cümleyle başlamıyor"],
        "assist_check": "pass",
        "discovery_check": "skipped",
        "format_check": "pass",
        "assist": {"kind": "disambiguate", "question": _Q, "available": []},
        "phrase_check": "skipped",
        "value_check": "fail",
        "value_check_reason": "expected value text not found in answer",
        "passed": False,
        "error": None,
        "latency_ms": 1900,
        "tokens_in": 2019,
        "tokens_out": 70,
        "model": "claude-haiku-5-5",
    }
    row.update(overrides)
    return row


def _audit_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": "11111111-1111-1111-1111-111111111111",
        "timestamp": "2026-10-14T19:31:00+00:00",
        "request_id": "req-1",
        "question": "Kredi sözleşmesinin vadesi kaç yıl?",
        "query_type": "DOCUMENT_QUERY",
        "answer": _Q,
        "sources": [],
        "excel_files_used": [],
        "documents_retrieved": ["d1"],
        "chunks_retrieved": [],
        "assist": {"kind": "disambiguate", "question": _Q, "available": []},
    }
    row.update(overrides)
    return row


def test_align_requires_matching_question_and_answer_text() -> None:
    assert rescore.align([_old_row()], [_audit_row()])
    with pytest.raises(SystemExit, match="disagree"):
        rescore.align([_old_row()], [_audit_row(answer="başka")])
    with pytest.raises(SystemExit, match="results vs"):
        rescore.align([_old_row()], [])


def test_outcome_is_rebuilt_from_the_audit_sources() -> None:
    audit = _audit_row(
        sources=[{"title": "Facility Agreement", "document_id": "doc-1", "page_number": 3}],
        excel_files_used=["Covenant_Report.xlsx"],
    )
    outcome = rescore.outcome_from(_old_row(answered=True, answer_text=_Q), audit)
    assert outcome.answered and outcome.cited_titles == ("Facility Agreement",)
    assert outcome.cited_files == ("Covenant_Report.xlsx",)
    assert outcome.cited_pages == (("doc-1", 3),)
    assert outcome.audit_log_id == "11111111-1111-1111-1111-111111111111"
    assert outcome.request_id == "req-1" and outcome.retrieved_document_ids == ("d1",)
    assert outcome.assist == {"kind": "disambiguate", "question": _Q, "available": []}


def _result(**overrides: object) -> QuestionResult:
    base: dict[str, object] = {
        "id": "ANK-NEG-003",
        "category": "document",
        "ask_as_user": "finans",
        "question": "q",
        "expect_no_answer": True,
        "answered": False,
        "answer_text": _Q,
        "cited_titles": (),
        "answered_ok": True,
        "required_sources_missing": (),
        "forbidden_sources_hit": (),
        "value_check": "skipped",
        "value_check_reason": "expect_no_answer + expect_assist",
        "passed": True,
        "error": None,
        "latency_ms": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "model": None,
        "safety_check": "pass",
        "safety_reasons": (),
    }
    base.update(overrides)
    return QuestionResult(**base)  # type: ignore[arg-type]


def test_changed_rules_are_derived_from_the_check_fields() -> None:
    assert rescore.changed_rules(_old_row(), _result(), question_changed=False) == ["A1", "A3"]
    old = _old_row(
        safety_reasons=["G3: yetkisiz belge önerildi: Financial Model 2026"],
        value_check="skipped",
    )
    assert rescore.changed_rules(old, _result(), question_changed=False) == ["A2"]
    old = _old_row(
        safety_reasons=["G3: yasak kaynak assist'te: Facility Agreement"], value_check="skipped"
    )
    assert rescore.changed_rules(old, _result(), question_changed=True) == ["A4", "B"]
    old = _old_row(
        required_sources_missing=["Aylık Üretim Raporu — Aralık 2023"],
        safety_reasons=[],
        value_check="pass",
    )
    assert rescore.changed_rules(old, _result(value_check="pass", source_rule="set"), False) == [
        "A5"
    ]
    assert (
        rescore.changed_rules(old, _result(value_check="pass", source_rule="strict"), False) == []
    )


def test_no_db_rescore_end_to_end(tmp_path: Path) -> None:
    """ANK-NEG-003 as S3 gave it: the bare disambiguate question failed on G2 + value check;
    under v2.0 (A1 + A3) it passes. `--no-db` leaves the safety checks "skipped" and is a dry
    run only (documented) — the diff, cost and controller files are still produced."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "results.json").write_text(
        json.dumps(
            {
                "model": "fixture",
                "date": "2026-10-14",
                "demo_today": "2026-10-06",
                "embeddings_enabled": False,
                "categories": [
                    {"category": "document", "total": 1, "evaluated": 1, "passed": 0, "errored": 0}
                ],
                "questions": [_old_row()],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    audit = tmp_path / "audit.jsonl"
    audit.write_text(json.dumps(_audit_row(), ensure_ascii=False) + "\n", encoding="utf-8")
    llm_log = tmp_path / "backend.log"
    llm_log.write_text(
        '{"message": "llm call", "request_id": "req-1", "model": "claude-haiku-5-5", '
        '"tokens_in": 2019, "tokens_out": 70}\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    code = rescore.main(
        [
            "--results",
            str(run_dir),
            "--audit",
            str(audit),
            "--out",
            str(out),
            "--llm-log",
            str(llm_log),
            "--controller-sample",
            "1",
            "--no-db",
        ]
    )
    assert code == 0
    payload = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert payload["scorer_version"] == "2.0"
    row = payload["questions"][0]
    assert row["passed"] is True and row["value_check"] == "skipped"
    assert row["safety_check"] == "skipped"  # --no-db
    diff = (out / "rescore_diff.md").read_text(encoding="utf-8")
    assert (
        "Önce 0/1 → sonra 1/1" in diff and "| ANK-NEG-003 | document | ❌ | ✅ | A1, A3 |" in diff
    )
    cost = json.loads((out / "cost.json").read_text(encoding="utf-8"))
    assert cost["by_model"]["claude-haiku-5-5"]["calls"] == 1
    assert (out / "kontrolor_1.md").exists()
