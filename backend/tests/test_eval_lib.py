"""Phase 4.1 eval runner — pure scoring logic (no network, no DB). Exercises both the
real committed `questions.json`/`seed_data/master/*.yaml` (the ground truth this tool
scores against) and hand-built `Question`/`AskOutcome` fixtures for the scoring rules
themselves."""

from __future__ import annotations

from scripts.eval_lib import (
    AskOutcome,
    DocumentCatalog,
    _classify_and_format,
    _normalize,
    _source_satisfied,
    build_document_catalog,
    build_report,
    load_ledger_raws,
    load_questions,
    render_markdown,
    report_to_json,
    resolve_expected,
    score_question,
    value_check_passes,
)
from seed_data.generator import ledger_schema as ls


def _question(**overrides: object) -> ls.Question:
    defaults: dict[str, object] = {
        "id": "ANK-XXX-001",
        "category": "document",
        "question": "test?",
        "expected_answer": None,
        "expected_answer_aliases": [],
        "expected_project": "Ankara RES",
        "expected_department": "finans",
        "required_sources": [],
        "forbidden_sources": [],
        "ask_as_user": "finans",
        "expect_no_answer": False,
        "notes": None,
    }
    defaults.update(overrides)
    return ls.Question.model_validate(defaults)


# ---------------------------------------------------------------- loading real data


def test_load_questions_returns_the_committed_43_questions() -> None:
    question_set = load_questions()
    assert len(question_set.questions) == 48  # v2: +3 data +2 mixed (Phase 4.3)
    assert question_set.version == 2


def test_build_document_catalog_maps_title_type_and_project() -> None:
    catalog = build_document_catalog()
    assert catalog.title_to_type["Facility Agreement Amendment 01"] == "Facility Agreement"
    # "Facility Agreement" is a type shared by three distinct documents (base + 2 amendments).
    facility_titles = {t for t, k in catalog.title_to_type.items() if k == "Facility Agreement"}
    assert len(facility_titles) >= 3
    assert catalog.title_to_project["Ankara RES Üretim Lisansı"] == "Ankara RES"
    # Phase 4.3: workbooks join the catalog; `excel_sources` cite them by file name.
    assert catalog.file_to_title["Covenant_Report.xlsx"] == "Covenant Report (workbook)"
    assert catalog.title_to_type["Budget vs Actual 2026"] == "Budget vs Actual"
    assert catalog.title_to_project["Monthly Production 2026"] == "Ankara RES"
    assert catalog.title_to_project["İzmir RES Önlisans Belgesi"] == "İzmir RES"
    assert catalog.project_names == {"Ankara RES", "İzmir RES"}


def test_cited_workbook_file_satisfies_a_required_workbook_title() -> None:
    """A MIXED answer cites the amendment page *and* `Covenant_Report.xlsx` — both
    required sources are satisfied, and the report lists the workbook's title."""
    from scripts.eval_lib import ExpectedValue

    catalog = DocumentCatalog(
        title_to_type={
            "Facility Agreement Amendment 01": "Facility Agreement",
            "Covenant Report (workbook)": "Covenant Report",
        },
        title_to_project={},
        file_to_title={"Covenant_Report.xlsx": "Covenant Report (workbook)"},
    )
    question = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    outcome = AskOutcome(
        answered=True,
        answer_text="Belgelere göre: 1,20x [K1].\n\nExcel verisine göre: 1,37x.",
        cited_titles=("Facility Agreement Amendment 01",),
        cited_files=("Covenant_Report.xlsx",),
        query_type="MIXED_QUERY",
    )
    result = score_question(question, ExpectedValue(required=(("1,20x",),)), catalog, outcome)
    assert result.passed and result.required_sources_missing == ()
    assert result.cited_titles == ("Covenant Report (workbook)", "Facility Agreement Amendment 01")
    assert result.query_type == "MIXED_QUERY"

    without_excel = AskOutcome(
        answered=True, answer_text="1,20x [K1]", cited_titles=("Facility Agreement Amendment 01",)
    )
    result = score_question(question, ExpectedValue(skip=True), catalog, without_excel)
    assert not result.passed and result.required_sources_missing == ("Covenant Report (workbook)",)


# ---------------------------------------------------------------- resolve_expected (real ledger)


def test_resolve_expected_formats_date_like_the_prompt_instructs() -> None:
    raws = load_ledger_raws()
    question = _question(
        id="ANK-DEV-002", expected_answer="ledger:ankara_res.project.timeline.licence.date"
    )
    expected = resolve_expected(question, raws)
    assert not expected.skip
    assert expected.required == (("15.06.2020", "2020-06-15", "June 15, 2020"),)


def test_resolve_expected_formats_ratio_with_a_dot_decimal_alias() -> None:
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-006",
        expected_answer="ledger:ankara_res.project.finance.dscr_covenant.current.value",
    )
    expected = resolve_expected(question, raws)
    assert expected.required == (("1,20x", "1.20x"),)


def test_resolve_expected_accepts_grouped_and_ungrouped_mwh() -> None:
    """Documents print `13538 MWh`, the Excel engine relays `13.538 MWh` (Phase 4.3 eval)."""
    raws = load_ledger_raws()
    question = _question(
        id="ANK-DAT-002",
        expected_answer="ledger:ankara_res.project.operations.monthly_production[33].mwh",
    )
    expected = resolve_expected(question, raws)
    assert expected.required == (("13538 MWh", "13.538 MWh"),)


def test_resolve_expected_formats_money_with_the_ledgers_own_currency() -> None:
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-002", expected_answer="ledger:ankara_res.project.finance.total_debt.value"
    )
    expected = resolve_expected(question, raws)
    assert expected.required == (("50.400.000 EUR", "50,400,000 EUR"),)


def test_value_check_passes_accepts_the_english_thousands_grouping_of_a_money_figure() -> None:
    """Live finding (`ANK-FIN-011`, 24.09.2026 eval run): the model sometimes relays a
    money figure exactly as printed in the (English) source document, comma-grouped,
    instead of reformatting it to TR dot-grouping."""
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-011",
        expected_answer="ledger:ankara_res.project.finance.outstanding_debt_as_of_demo_today.value",
    )
    expected = resolve_expected(question, raws)
    assert value_check_passes(expected, "Güncel kalan borç 44,100,000 EUR'dur.")
    assert value_check_passes(expected, "Güncel kalan borç 44.100.000 EUR'dur.")


def test_resolve_expected_handles_the_initial_current_compound_value() -> None:
    """ANK-FIN-013 asks for two values in one question ("ilk ne kadardı, şimdi ne
    kadar?") — the ledger path deliberately resolves to a dict, not a scalar (see the
    question's own `notes` field). Both formatted values must be required, independently."""
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-013", expected_answer="ledger:ankara_res.project.finance.tenor_years"
    )
    expected = resolve_expected(question, raws)
    assert not expected.skip
    assert expected.required == (("12 yıl",), ("14 yıl",))


def test_resolve_expected_skips_a_list_value() -> None:
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-009", expected_answer="ledger:ankara_res.project.finance.facility_chain"
    )
    expected = resolve_expected(question, raws)
    assert expected.skip
    assert expected.required == ()


def test_resolve_expected_skips_a_doc_id_reference() -> None:
    raws = load_ledger_raws()
    question = _question(
        id="ANK-EPC-002",
        expected_answer="ledger:ankara_res.project.construction.epc_contract_current_doc",
    )
    expected = resolve_expected(question, raws)
    assert expected.skip
    assert expected.skip_reason is not None


def test_resolve_expected_none_answer_skips_value_check() -> None:
    question = _question(id="GEN-HAL-001", expected_answer=None, expect_no_answer=True)
    expected = resolve_expected(question, {})
    assert expected.skip
    assert expected.skip_reason == "expect_no_answer"


def test_every_question_with_a_ledger_expected_answer_resolves_without_error() -> None:
    """Smoke test over the full real dataset: `resolve_expected` must never raise, even
    if it ends up skipping most of them."""
    raws = load_ledger_raws()
    for question in load_questions().questions:
        resolve_expected(question, raws)  # no exception


def test_classify_and_format_rejects_bools_and_free_text() -> None:
    assert _classify_and_format(True, "project.some_flag", None) is None
    assert _classify_and_format("free text sentence", "project.notes", None) is None


# ---------------------------------------------------------------- value_check_passes


def test_value_check_passes_ignores_case_and_whitespace() -> None:
    from scripts.eval_lib import ExpectedValue

    expected = ExpectedValue(required=(("1,20x", "1.20x"),))
    assert value_check_passes(expected, "Güncel  DSCR   1,20X'tir.")
    assert not value_check_passes(expected, "Güncel DSCR 1,25x'tir.")


def test_value_check_passes_requires_every_group_for_compound_values() -> None:
    from scripts.eval_lib import ExpectedValue

    expected = ExpectedValue(required=(("12 yıl",), ("14 yıl",)))
    assert value_check_passes(expected, "İlk tenor 12 yıl idi, şimdi 14 yıl.")
    assert not value_check_passes(expected, "İlk tenor 12 yıl idi.")


def test_normalize_collapses_whitespace() -> None:
    assert _normalize("  a   b\nc  ") == "a b c"


# ---------------------------------------------------------------- source matching


def test_source_satisfied_matches_exact_title() -> None:
    catalog = DocumentCatalog(
        title_to_type={"Facility Agreement Amendment 01": "Facility Agreement"},
        title_to_project={"Facility Agreement Amendment 01": "Ankara RES"},
    )
    cited = frozenset({"Facility Agreement Amendment 01"})
    assert _source_satisfied("Facility Agreement Amendment 01", cited, catalog)
    assert not _source_satisfied("Facility Agreement Amendment 02", cited, catalog)


def test_source_satisfied_matches_by_document_type() -> None:
    catalog = DocumentCatalog(
        title_to_type={"Facility Agreement": "Facility Agreement", "EPC Contract": "EPC Contract"},
        title_to_project={"Facility Agreement": "Ankara RES", "EPC Contract": "Ankara RES"},
    )
    cited = frozenset({"EPC Contract"})
    assert not _source_satisfied("Facility Agreement", cited, catalog)
    cited = frozenset({"Facility Agreement"})
    assert _source_satisfied("Facility Agreement", cited, catalog)


def test_source_name_that_is_both_a_title_and_a_type_accepts_either_reading() -> None:
    catalog = DocumentCatalog(
        title_to_type={
            "Facility Agreement": "Facility Agreement",
            "Facility Agreement — Draft": "Facility Agreement",
        },
        title_to_project={},
    )
    assert _source_satisfied(
        "Facility Agreement", frozenset({"Facility Agreement — Draft"}), catalog
    )
    assert not _source_satisfied("Facility Agreement", frozenset({"EPC Contract"}), catalog)


def test_source_satisfied_matches_by_project_name() -> None:
    catalog = DocumentCatalog(
        title_to_type={"İzmir RES Önlisans Belgesi": "Önlisans"},
        title_to_project={"İzmir RES Önlisans Belgesi": "İzmir RES"},
    )
    assert _source_satisfied("İzmir RES", frozenset({"İzmir RES Önlisans Belgesi"}), catalog)
    assert not _source_satisfied("İzmir RES", frozenset(), catalog)


def test_source_satisfied_unknown_name_never_matches() -> None:
    catalog = DocumentCatalog(title_to_type={}, title_to_project={})
    assert not _source_satisfied("Nonexistent Document", frozenset({"anything"}), catalog)


# ---------------------------------------------------------------- score_question


def _catalog() -> DocumentCatalog:
    return DocumentCatalog(
        title_to_type={
            "Facility Agreement Amendment 01": "Facility Agreement",
            "İzmir RES Önlisans Belgesi": "Önlisans",
        },
        title_to_project={
            "Facility Agreement Amendment 01": "Ankara RES",
            "İzmir RES Önlisans Belgesi": "İzmir RES",
        },
    )


def test_score_question_passes_when_sources_and_value_match() -> None:
    from scripts.eval_lib import ExpectedValue

    question = _question(required_sources=["Facility Agreement Amendment 01"], forbidden_sources=[])
    expected = ExpectedValue(required=(("1,20x",),))
    outcome = AskOutcome(
        answered=True,
        answer_text="Güncel DSCR 1,20x'tir [K1].",
        cited_titles=("Facility Agreement Amendment 01",),
        model="gemini-3.5-flash-lite",
        tokens_in=100,
        tokens_out=20,
        latency_ms=500,
    )
    result = score_question(question, expected, _catalog(), outcome)
    assert result.passed
    assert result.value_check == "pass"
    assert result.error is None


def test_score_question_fails_when_required_source_missing() -> None:
    from scripts.eval_lib import ExpectedValue

    question = _question(required_sources=["Facility Agreement Amendment 01"])
    expected = ExpectedValue(skip=True, skip_reason="test")
    outcome = AskOutcome(answered=True, answer_text="cevap", cited_titles=())
    result = score_question(question, expected, _catalog(), outcome)
    assert not result.passed
    assert result.required_sources_missing == ("Facility Agreement Amendment 01",)


def test_score_question_fails_when_forbidden_source_cited() -> None:
    from scripts.eval_lib import ExpectedValue

    question = _question(forbidden_sources=["İzmir RES"])
    expected = ExpectedValue(skip=True, skip_reason="test")
    outcome = AskOutcome(
        answered=True, answer_text="cevap", cited_titles=("İzmir RES Önlisans Belgesi",)
    )
    result = score_question(question, expected, _catalog(), outcome)
    assert not result.passed
    assert result.forbidden_sources_hit == ("İzmir RES",)


def test_score_question_fails_when_answered_does_not_match_expectation() -> None:
    from scripts.eval_lib import ExpectedValue

    question = _question(expect_no_answer=True)
    expected = ExpectedValue(skip=True, skip_reason="test")
    outcome = AskOutcome(answered=True, answer_text="cevap", cited_titles=())
    result = score_question(question, expected, _catalog(), outcome)
    assert not result.passed
    assert not result.answered_ok


def test_score_question_can_pass_with_a_skipped_value_check() -> None:
    """SORU 1 (approved): a skipped value check is neutral, not a failure, as long as
    sources + answered are correct."""
    from scripts.eval_lib import ExpectedValue

    question = _question()
    expected = ExpectedValue(skip=True, skip_reason="unformattable")
    outcome = AskOutcome(answered=True, answer_text="cevap", cited_titles=())
    result = score_question(question, expected, _catalog(), outcome)
    assert result.passed
    assert result.value_check == "skipped"


def test_score_question_request_error_is_never_passed() -> None:
    from scripts.eval_lib import ExpectedValue

    question = _question()
    expected = ExpectedValue(required=(("x",),))
    outcome = AskOutcome(error="http 503: unavailable")
    result = score_question(question, expected, _catalog(), outcome)
    assert not result.passed
    assert result.error == "http 503: unavailable"


# ---------------------------------------------------------------- build_report / rendering


def test_build_report_applies_100pct_and_80pct_thresholds() -> None:
    hallucination_pass = score_question(
        _question(id="GEN-HAL-001", category="hallucination", expect_no_answer=True),
        resolve_expected(_question(expected_answer=None, expect_no_answer=True), {}),
        _catalog(),
        AskOutcome(answered=False, answer_text="bulunamadı"),
    )
    document_fail = score_question(
        _question(id="ANK-DOC-001", category="document", required_sources=["Missing Doc"]),
        resolve_expected(_question(expected_answer=None), {}),
        _catalog(),
        AskOutcome(answered=True, answer_text="cevap", cited_titles=()),
    )
    report = build_report(
        [hallucination_pass, document_fail],
        model="gemini-3.5-flash-lite",
        date_str="2026-09-24",
        demo_today="2026-09-15",
        embeddings_enabled=False,
    )
    by_category = {c.category: c for c in report.categories}
    assert by_category["hallucination"].threshold_pct == 100.0
    assert by_category["hallucination"].meets_threshold
    assert by_category["document"].threshold_pct == 80.0
    assert not by_category["document"].meets_threshold
    assert not report.ok


def test_build_report_excludes_errored_questions_from_the_denominator() -> None:
    errored = score_question(
        _question(id="ANK-DOC-002", category="document"),
        resolve_expected(_question(expected_answer=None), {}),
        _catalog(),
        AskOutcome(error="timeout"),
    )
    report = build_report(
        [errored],
        model="m",
        date_str="2026-09-24",
        demo_today="2026-09-15",
        embeddings_enabled=False,
    )
    category = report.categories[0]
    assert category.total == 1
    assert category.evaluated == 0
    assert category.errored == 1
    assert not category.meets_threshold  # 0 evaluated -> never meets a threshold


def test_render_markdown_and_report_to_json_do_not_raise() -> None:
    result = score_question(
        _question(id="ANK-DOC-003", category="document"),
        resolve_expected(_question(expected_answer=None), {}),
        _catalog(),
        AskOutcome(answered=True, answer_text="cevap", cited_titles=()),
    )
    report = build_report(
        [result],
        model="gemini-3.5-flash-lite",
        date_str="2026-09-24",
        demo_today="2026-09-15",
        embeddings_enabled=True,
        partial=True,
        partial_reason="test",
    )
    markdown = render_markdown(report)
    assert "gemini-3.5-flash-lite" in markdown
    assert "Koşu yarıda kesildi" in markdown
    payload = report_to_json(report)
    assert payload["ok"] is True  # the one question in this report passes
    assert payload["partial"] is True
    assert len(payload["questions"]) == 1


# ---------------------------------------------------------------- Phase 3.2b


def test_target_index_finds_the_page_that_prints_a_key_fact() -> None:
    from scripts.eval_lib import build_target_index, target_pages

    raws = {
        "ankara_res": {
            "documents": [
                {"id": "DOC-X", "key_facts": {"total_debt": "project.finance.total_debt.value"}}
            ]
        }
    }
    manifest = {
        "documents": [
            {
                "external_ref": "DOC-X",
                "title": "FA",
                "key_facts_used": {"total_debt": "50,400,000 EUR"},
            }
        ]
    }
    page_texts = {"FA": [(1, "cover"), (4, "structured as 50,400,000 EUR in total")]}
    index = build_target_index(raws, manifest, page_texts)
    question = _question(expected_answer="ledger:ankara_res.project.finance.total_debt.value")
    assert target_pages(question, index) == {("FA", 4)}
    # A compound path (initial/current) is matched by prefix.
    question = _question(expected_answer="ledger:ankara_res.project.finance.total_debt")
    assert target_pages(question, index) == {("FA", 4)}


def test_target_pages_falls_back_to_expected_text_in_required_sources() -> None:
    from scripts.eval_lib import ExpectedValue, TargetIndex, target_pages

    catalog = DocumentCatalog(title_to_type={"FA": "Facility Agreement"}, title_to_project={})
    question = _question(
        expected_answer="ledger:ankara_res.project.timeline.financial_close.date",
        required_sources=["Facility Agreement"],
    )
    expected = ExpectedValue(required=(("15.11.2021", "2021-11-15", "November 15, 2021"),))
    page_texts = {"FA": [(1, "Financial close occurred on November 15, 2021."), (2, "other")]}
    pages = target_pages(
        question, TargetIndex({}), expected=expected, catalog=catalog, page_texts=page_texts
    )
    assert pages == {("FA", 1)}


def test_name_path_resolves_to_a_literal_spelling() -> None:
    raws = load_ledger_raws()
    question = _question(id="ANK-ISO-002", expected_answer="ledger:ankara_res.project.name")
    expected = resolve_expected(question, raws)
    assert expected.required == (("Ankara RES",),)


def test_summarize_consistency_separates_retrieval_from_model() -> None:
    from scripts.eval_lib import RepeatOutcome, summarize_consistency

    outcomes = [
        RepeatOutcome("Q1", 1, True, True, True, None),
        RepeatOutcome("Q1", 2, True, False, False, None),  # page present, model refused
        RepeatOutcome("Q1", 3, True, True, True, None),
        RepeatOutcome("Q2", 1, True, True, True, None),
        RepeatOutcome("Q2", 2, False, False, False, None),  # retrieval miss
        RepeatOutcome("Q2", 3, True, True, True, None),
        RepeatOutcome("Q3", 1, None, False, None, "http 503"),
    ]
    s = summarize_consistency(outcomes)
    assert (s.retrieval_stable, s.retrieval_measurable) == (1, 2)
    assert (s.model_answered, s.model_measurable) == (4, 5)
    assert (s.value_ok, s.value_measurable) == (4, 6)
