"""Phase 4.1 eval runner — pure scoring logic (no network, no DB). Exercises both the
real committed `questions.json`/`seed_data/master/*.yaml` (the ground truth this tool
scores against) and hand-built `Question`/`AskOutcome` fixtures for the scoring rules
themselves."""

from __future__ import annotations

from scripts.eval_lib import (
    AskOutcome,
    DocumentCatalog,
    SafetyContext,
    _classify_and_format,
    _normalize,
    _source_satisfied,
    assist_check,
    build_document_catalog,
    build_report,
    fact_tokens,
    load_ledger_raws,
    load_questions,
    phrase_check_passes,
    render_markdown,
    report_to_json,
    resolve_expected,
    safety_checks,
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
        "expected_project": "Karatepe RES",
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


def test_load_questions_returns_the_committed_questions() -> None:
    question_set = load_questions()
    # v5 (ADR-027): 64 + 5 ambiguous + 4 term_mismatch + 1 temporal (rule 8) + 2 negative controls;
    # v6 (BELIRSIZLIK_PLAN §3): + 3 negative controls + GEN-AMB-003-F (same question, finance user)
    # v7 (Tansu Ürün 1 §B, B ölçümü): + 13 discovery
    # v8 (B ölçümü teşhis tekrarı): + 5 düzeltilmiş teşhis varyantı; held_out +6 discovery
    # v9 (Adım 4, ADR-030): + GEN-AMB-006 (belge-varlığı kriteriyle seçilen dev AMB sorusu)
    # v10 (Adım 5 İş 3): ANK-FIN-013 tenor_years -> margin_pct (tenor fiilen değişmedi,
    # F4 kuralı tarafından zaten tek değer olarak değerlendiriliyordu; margin gerçek bir
    # initial != current çifti ve henüz test edilmemişti); soru sayısı değişmedi (99)
    assert len(question_set.questions) == 99
    assert question_set.version == 10


def test_build_document_catalog_maps_title_type_and_project() -> None:
    catalog = build_document_catalog()
    assert catalog.title_to_type["Facility Agreement Amendment 01"] == "Facility Agreement"
    # "Facility Agreement" is a type shared by three distinct documents (base + 2 amendments).
    facility_titles = {t for t, k in catalog.title_to_type.items() if k == "Facility Agreement"}
    assert len(facility_titles) >= 3
    assert catalog.title_to_project["Karatepe RES Üretim Lisansı"] == "Karatepe RES"
    # Phase 4.3: workbooks join the catalog; `excel_sources` cite them by file name.
    assert catalog.file_to_title["Covenant_Report.xlsx"] == "Covenant Report (workbook)"
    assert catalog.title_to_type["Budget vs Actual 2026"] == "Budget vs Actual"
    assert catalog.title_to_project["Monthly Production 2026"] == "Karatepe RES"
    assert catalog.title_to_project["Kızılova RES Önlisans Belgesi"] == "Kızılova RES"
    assert catalog.project_names == {"Karatepe RES", "Kızılova RES"}


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
    assert expected.required == (("13.600.000 USD", "13,600,000 USD"),)


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
    assert value_check_passes(expected, "Güncel kalan borç 11,671,800 USD'dur.")
    assert value_check_passes(expected, "Güncel kalan borç 11.671.800 USD'dur.")


def test_resolve_expected_handles_the_initial_current_compound_value() -> None:
    """A question asking for two values in one go ("ilk ne kadardı, şimdi ne kadar?") —
    the ledger path deliberately resolves to a dict, not a scalar. Both formatted values
    must be required, independently. Synthetic fixture id (not the real ANK-FIN-013,
    which now exercises margin_pct — see test below); dscr_covenant (1.25 -> 1.20) is
    just a convenient other compound field to exercise the same generic behavior."""
    raws = load_ledger_raws()
    question = _question(
        id="ANK-XXX-013", expected_answer="ledger:ankara_res.project.finance.dscr_covenant"
    )
    expected = resolve_expected(question, raws)
    assert not expected.skip
    assert expected.required == (("1,25x", "1.25x"), ("1,20x", "1.20x"))


def test_resolve_expected_handles_ank_fin_013_margin_pct() -> None:
    """v10 (Adım 5 İş 3): ANK-FIN-013 moved from tenor_years (no longer changes for
    Karatepe, 13 -> 13) to margin_pct (3.25% -> 2.90%, DOC-ANK-FIN-006) — the one
    remaining initial != current compound field not already covered by another
    question (dscr_covenant: ANK-FIN-006/007; capacity_mw: ANK-DEV-003/004/006,
    ANK-EPC-005)."""
    raws = load_ledger_raws()
    question = _question(
        id="ANK-FIN-013",
        expected_answer="ledger:ankara_res.project.finance.interest.margin_pct",
    )
    expected = resolve_expected(question, raws)
    assert not expected.skip
    assert expected.required == (("%3,25", "%3.25"), ("%2,9", "%2.9"))


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


def test_resolve_expected_literal_answer_accepts_its_own_aliases() -> None:
    """Adım 5 Aşama C.5 (10.10.2026, ANK-FIN-004): a non-`ledger:` expected_answer has no
    single canonical phrasing — `expected_answer_aliases` gives acceptable alternatives,
    any one of which satisfies the check."""
    question = _question(
        id="ANK-FIN-004",
        expected_answer="ECA tranşı yok",
        expected_answer_aliases=["ECA katılımı yok", "ECA kullandırılmadı"],
    )
    expected = resolve_expected(question, {})
    assert not expected.skip
    assert expected.required == (("ECA tranşı yok", "ECA katılımı yok", "ECA kullandırılmadı"),)
    assert value_check_passes(expected, "Hayır, ECA katılımı yok.")
    assert not value_check_passes(expected, "Evet, 5.000.000 USD ECA tranşı vardır.")


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
        title_to_project={"Facility Agreement Amendment 01": "Karatepe RES"},
    )
    cited = frozenset({"Facility Agreement Amendment 01"})
    assert _source_satisfied("Facility Agreement Amendment 01", cited, catalog)
    assert not _source_satisfied("Facility Agreement Amendment 02", cited, catalog)


def test_source_satisfied_matches_by_document_type() -> None:
    catalog = DocumentCatalog(
        title_to_type={"Facility Agreement": "Facility Agreement", "EPC Contract": "EPC Contract"},
        title_to_project={"Facility Agreement": "Karatepe RES", "EPC Contract": "Karatepe RES"},
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
        title_to_type={"Kızılova RES Önlisans Belgesi": "Önlisans"},
        title_to_project={"Kızılova RES Önlisans Belgesi": "Kızılova RES"},
    )
    assert _source_satisfied("Kızılova RES", frozenset({"Kızılova RES Önlisans Belgesi"}), catalog)
    assert not _source_satisfied("Kızılova RES", frozenset(), catalog)


def test_source_satisfied_unknown_name_never_matches() -> None:
    catalog = DocumentCatalog(title_to_type={}, title_to_project={})
    assert not _source_satisfied("Nonexistent Document", frozenset({"anything"}), catalog)


# ---------------------------------------------------------------- score_question


def _catalog() -> DocumentCatalog:
    return DocumentCatalog(
        title_to_type={
            "Facility Agreement Amendment 01": "Facility Agreement",
            "Kızılova RES Önlisans Belgesi": "Önlisans",
        },
        title_to_project={
            "Facility Agreement Amendment 01": "Karatepe RES",
            "Kızılova RES Önlisans Belgesi": "Kızılova RES",
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

    question = _question(forbidden_sources=["Kızılova RES"])
    expected = ExpectedValue(skip=True, skip_reason="test")
    outcome = AskOutcome(
        answered=True, answer_text="cevap", cited_titles=("Kızılova RES Önlisans Belgesi",)
    )
    result = score_question(question, expected, _catalog(), outcome)
    assert not result.passed
    assert result.forbidden_sources_hit == ("Kızılova RES",)


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
    assert expected.required == (("Karatepe RES",),)


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


def _comparison_question(**overrides: object) -> ls.Question:
    base: dict[str, object] = {
        "id": "GEN-CMP-999",
        "category": "comparison",
        "question": "A ile B — hangisi?",
        "expected_answer": [
            "ledger:ankara_res.project.timeline.licence.date",
            "ledger:izmir_res.project.timeline.pre_licence.date",
        ],
        "expected_answer_aliases": [],
        "expected_project": None,
        "expected_department": "enerji_grubu",
        "required_sources": [],
        "forbidden_sources": [],
        "ask_as_user": "enerji",
        "expect_no_answer": False,
        "required_phrases": ["Projeler arası karşılaştırma bu üründe yapılmaz"],
        "forbidden_phrases": ["daha önce", "daha sonra"],
    }
    base.update(overrides)
    return ls.Question.model_validate(base)


def test_resolve_expected_accepts_a_list_of_ledger_facts_one_group_each() -> None:
    raws = load_ledger_raws()
    expected = resolve_expected(_comparison_question(), raws)
    assert not expected.skip and len(expected.required) == 2
    assert "15.06.2020" in expected.required[0]  # Ankara licence date, TR form
    assert value_check_passes(expected, "15.06.2020 … 18.01.2024")
    assert not value_check_passes(expected, "15.06.2020 yalnızca")


def test_phrase_check_requires_the_notice_and_rejects_comparatives() -> None:
    q = _comparison_question()
    ok, reason = phrase_check_passes(
        q,
        "Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır. "
        "A: x. B: y.",
    )
    assert ok and reason is None
    ok, reason = phrase_check_passes(q, "A: x. B: y. A DAHA ÖNCE alınmıştır.")
    assert not ok and "eksik ifade" in str(reason) and "yasak ifade" in str(reason)
    ok, _ = phrase_check_passes(_comparison_question(required_phrases=[]), "A: x. B: y.")
    assert ok


# ---------------------------------------------------------------- ADR-027: G1–G3 invariants


def _mini_catalog() -> DocumentCatalog:
    return DocumentCatalog(
        title_to_type={"Facility Agreement": "Facility Agreement", "Önlisans": "Önlisans"},
        title_to_project={"Facility Agreement": "Karatepe RES", "Önlisans": "Kızılova RES"},
    )


def test_fact_tokens_normalise_date_and_number_spellings() -> None:
    """Naci (05.10.2026): `10 Ocak 2025`, `10.01.2025`, `2025-01-10` are one token; thousands
    separators and the decimal comma never cause a false alarm."""
    assert fact_tokens("10 Ocak 2025") == fact_tokens("10.01.2025") == fact_tokens("2025-01-10")
    assert fact_tokens("44.100.000 EUR") == fact_tokens("44,100,000 EUR") == {"44100000"}
    assert fact_tokens("DSCR 1,37x") == fact_tokens("DSCR 1.37x") == {"1.37"}
    assert fact_tokens("%38,2") == fact_tokens("38.2%") == {"38.2"}
    assert fact_tokens("Aralık 2023 üretimi") == {"2023-12"}
    # English finance documents: "November 15, 2021" == "15.11.2021"; labels are not numbers.
    assert fact_tokens("achieved on November 15, 2021") == fact_tokens("15.11.2021")
    assert fact_tokens("December 2021") == {"2021-12"}
    assert fact_tokens("Section AMD01, period Q2_2026, turbine T-07") == set()
    # A date never leaks its parts as separate numbers.
    assert "2025" not in fact_tokens("09.01.2025") and "9" not in fact_tokens("09.01.2025")


def test_value_check_accepts_another_spelling_of_the_expected_date() -> None:
    """R1: the model wrote "15 Kasım 2021" for an expected "15.11.2021" — same date."""
    from scripts.eval_lib import ExpectedValue

    expected = ExpectedValue(required=(("15.11.2021",),))
    assert value_check_passes(expected, "Finansman 15 Kasım 2021 tarihinde kapanmıştır [K1].")
    assert value_check_passes(expected, "Financial close: November 15, 2021 [K1].")
    assert not value_check_passes(expected, "Finansman 16 Kasım 2021 tarihinde kapanmıştır [K1].")


def test_safety_g1_flags_a_number_absent_from_the_cited_text() -> None:
    question = _question(expected_answer="x")
    ctx = SafetyContext(
        grounding_text="Facility Agreement Tarih: 15.06.2023 total debt EUR 44,100,000",
        visible_document_ids=frozenset({"d1"}),
    )
    grounded = AskOutcome(
        answered=True,
        answer_text="Toplam borç 44.100.000 EUR [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    assert safety_checks(question, grounded, _mini_catalog(), ctx) == ()
    fabricated = AskOutcome(
        answered=True,
        answer_text="Toplam borç 44.100.000 EUR, vade 2031 [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    reasons = safety_checks(question, fabricated, _mini_catalog(), ctx)
    assert len(reasons) == 1 and reasons[0].startswith("G1") and "2031" in reasons[0]
    # DATA answers carry DuckDB's figure, not chunk text — G1's number check does not apply.
    excel = AskOutcome(
        answered=True,
        answer_text="DSCR 1,37x.",
        cited_files=("Covenant_Report.xlsx",),
        query_type="DATA_QUERY",
    )
    assert safety_checks(question, excel, _mini_catalog(), ctx) == ()


def test_safety_g2_requires_citations_or_the_fixed_sentence() -> None:
    question = _question(expect_no_answer=True)
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset())
    unsourced = AskOutcome(answered=True, answer_text="Vade on yıl.", query_type="DOCUMENT_QUERY")
    assert any(r.startswith("G2") for r in safety_checks(question, unsourced, _mini_catalog(), ctx))
    chatty = AskOutcome(answered=False, answer_text="Bilmiyorum ama sanırım on yıl.")
    assert any(r.startswith("G2") for r in safety_checks(question, chatty, _mini_catalog(), ctx))
    # A MIXED no-answer wraps the fixed sentence under a heading — still the fixed sentence;
    # the same text from the plain document pipeline is NOT accepted (relaxation is MIXED-only).
    wrapped = (
        "Belgelere göre:\nMevcut şirket kaynaklarında bu soruyu güvenilir şekilde "
        "cevaplamak için yeterli bilgi bulamadım.\n\nExcel verisine göre:\nveri bulamadım."
    )
    mixed = AskOutcome(answered=False, answer_text=wrapped, query_type="MIXED_QUERY")
    assert safety_checks(question, mixed, _mini_catalog(), ctx) == ()
    plain = AskOutcome(answered=False, answer_text=wrapped, query_type="DOCUMENT_QUERY")
    assert any(r.startswith("G2") for r in safety_checks(question, plain, _mini_catalog(), ctx))
    fixed = AskOutcome(
        answered=False,
        answer_text="Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için "
        "yeterli bilgi bulamadım.",
    )
    assert safety_checks(question, fixed, _mini_catalog(), ctx) == ()


def test_safety_g3_rejects_hidden_wrong_project_and_forbidden_suggestions() -> None:
    question = _question(
        expect_no_answer=True,
        expected_project="Kızılova RES",
        forbidden_sources=["Facility Agreement"],
    )
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset({"vis"}))
    fixed = (
        "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli "
        "bilgi bulamadım."
    )
    bad = AskOutcome(
        answered=False,
        answer_text=fixed,
        assist={
            "kind": "term_mismatch",
            "question": "Hangi belgeyi soruyorsunuz?",
            "available": [
                {"document_id": "hidden", "title": "Gizli", "project_code": "IZM_RES"},
                {"document_id": "vis", "title": "Facility Agreement", "project_code": "ANK_RES"},
            ],
        },
    )
    reasons = safety_checks(question, bad, _mini_catalog(), ctx)
    assert any("yetkisiz" in r for r in reasons)
    assert any("başka projenin" in r for r in reasons)
    assert any("yasak kaynak" in r for r in reasons)
    with_digits = AskOutcome(
        answered=False, answer_text=fixed, assist={"kind": "clarify", "question": "2025 mi?"}
    )
    assert any("rakam" in r for r in safety_checks(question, with_digits, _mini_catalog(), ctx))
    clean = AskOutcome(
        answered=False,
        answer_text=fixed,
        assist={
            "kind": "clarify",
            "question": "Hangi belgeyi soruyorsunuz?",
            "available": [{"document_id": "vis", "title": "Önlisans", "project_code": "IZM_RES"}],
        },
    )
    assert safety_checks(question, clean, _mini_catalog(), ctx) == ()


def test_assist_check_and_safety_feed_the_pass_verdict() -> None:
    question = _question(category="ambiguous", expect_no_answer=True, expect_assist="clarify")
    fixed = (
        "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli "
        "bilgi bulamadım."
    )
    assert assist_check(question, AskOutcome(answered=False, answer_text=fixed)) == (
        "skipped",
        "assist bloğu yok (ASSIST_MODE kapalı?)",
    )
    assert assist_check(
        question, AskOutcome(answered=False, answer_text=fixed, assist={"kind": "clarify"})
    ) == ("pass", None)
    status, _ = assist_check(
        question, AskOutcome(answered=False, answer_text=fixed, assist={"kind": "term_mismatch"})
    )
    assert status == "fail"

    expected = resolve_expected(question, load_ledger_raws())
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset())
    leaking = AskOutcome(
        answered=False,
        answer_text=fixed,
        assist={"kind": "clarify", "available": [{"document_id": "x", "title": "T"}]},
    )
    result = score_question(question, expected, _mini_catalog(), leaking, ctx)
    assert result.answered_ok and result.assist_check == "pass"
    assert result.safety_check == "fail" and not result.passed
    # Without a context (flag-off regression run) safety is "skipped", never a silent pass.
    assert score_question(question, expected, _mini_catalog(), leaking).safety_check == "skipped"


def test_safety_g3_covers_not7_pending_documents() -> None:
    """Not 7 §3: a pending document shown next to the answer is held to the same gate and
    forbidden-source rule as `assist.available` (project is not checked — it may be unset)."""
    question = _question(expect_no_answer=True, forbidden_sources=["Facility Agreement"])
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset({"vis"}))
    fixed = (
        "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli "
        "bilgi bulamadım."
    )
    bad = AskOutcome(
        answered=False,
        answer_text=fixed,
        pending_documents=(
            {"document_id": "hidden", "title": "Gizli Taslak", "status": "ocr"},
            {"document_id": "vis", "title": "Facility Agreement", "status": "failed"},
        ),
    )
    reasons = safety_checks(question, bad, _mini_catalog(), ctx)
    assert any("yetkisiz bekleyen" in r for r in reasons)
    assert any("yasak kaynak bekleyen" in r for r in reasons)
    clean = AskOutcome(
        answered=False,
        answer_text=fixed,
        pending_documents=({"document_id": "vis", "title": "Önlisans Taslak", "status": "ocr"},),
    )
    assert safety_checks(question, clean, _mini_catalog(), ctx) == ()


def test_discovery_check_requires_a_shown_document_and_an_answer_or_question() -> None:
    """B ölçümü (Tansu Ürün 1 §B): a discovery question passes when a required document is
    surfaced (cited or in assist.available) AND Balbal either answers or asks; the fixed
    sentence alone fails."""
    from scripts.eval_lib import discovery_check

    question = _question(
        category="discovery",
        expect_no_answer=False,
        required_sources=["Facility Agreement"],
    )
    catalog = _mini_catalog()
    fixed = (
        "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli "
        "bilgi bulamadım."
    )
    alone = AskOutcome(answered=False, answer_text=fixed)
    assert discovery_check(question, alone, catalog)[0] == "fail"
    listed = AskOutcome(
        answered=False,
        answer_text=fixed,
        assist={
            "kind": "clarify",
            "question": "Hangi sözleşmeyi kastediyorsunuz?",
            "available": [{"document_id": "x", "title": "Facility Agreement"}],
        },
    )
    assert discovery_check(question, listed, catalog) == ("pass", None)
    listed_no_question = AskOutcome(
        answered=False,
        answer_text=fixed,
        assist={
            "kind": "clarify",
            "question": None,
            "available": [{"title": "Facility Agreement"}],
        },
    )
    assert discovery_check(question, listed_no_question, catalog)[0] == "fail"
    answered = AskOutcome(
        answered=True,
        answer_text="Kredi sözleşmesi mevcuttur [K1].",
        cited_titles=("Facility Agreement",),
    )
    assert discovery_check(question, answered, catalog) == ("pass", None)
    other = _question(category="document", expect_no_answer=False)
    assert discovery_check(other, answered, catalog) == ("skipped", None)


# --- ADR-030 (Ek-F): the new verdict sentence and the F-8 format check ---


def test_g2_accepts_the_ek_f_verdict_after_the_understood_line() -> None:
    from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
    from scripts.eval_lib import _starts_with_verdict

    assert _starts_with_verdict(NO_ANSWER_TEXT)
    assert _starts_with_verdict(NO_DATA_VERDICT + "\nElimde konuyla ilgili şunlar var:\nA")
    assert _starts_with_verdict("«amendment» ifadesini tadil olarak anladım.\n" + NO_DATA_VERDICT)
    assert not _starts_with_verdict("Elimde şunlar var:\nA\n" + NO_DATA_VERDICT)
    assert not _starts_with_verdict("Belgelerde bir şey yok.")


def test_format_check_flags_raw_spellings_and_passes_turkish_ones() -> None:
    from scripts.eval_lib import format_check

    assert format_check("Capex 72000000 EUR, kapanış 2021-11-15 00:00:00") == (
        "fail",
        "ISO tarih, saat, gruplanmamış sayı",
    )
    assert format_check("oran 38.2% ve 1,000,000 USD")[0] == "fail"
    assert format_check("72.000.000 EUR, 15.11.2021, %2,90, 1,20x, %38,2 [K1]") == ("pass", None)
    # document and invoice numbers are identifiers, not numbers
    assert format_check("Fatura ENR2026001121, sözleşme S-26-001, 44.100.000 EUR") == ("pass", None)
    assert format_check("") == ("pass", None)


# --- Adım 4 (ADR-030, 09.10.2026): expect_assist="disambiguate" ---


def test_assist_check_matches_the_disambiguate_kind() -> None:
    question = _question(category="ambiguous", expect_no_answer=True, expect_assist="disambiguate")
    fixed_question = "Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?"
    assert assist_check(
        question,
        AskOutcome(answered=False, answer_text=fixed_question, assist={"kind": "disambiguate"}),
    ) == ("pass", None)
    status, reason = assist_check(
        question,
        AskOutcome(answered=False, answer_text=fixed_question, assist={"kind": "clarify"}),
    )
    assert status == "fail" and reason is not None
    # G1: the disambiguate question itself carries no digit/date/currency fact
    from scripts.eval_lib import format_check

    assert format_check(fixed_question) == ("pass", None)
