"""Phase 4.1 eval runner — pure scoring logic (no network, no DB). Exercises both the
real committed `questions.json`/`seed_data/master/*.yaml` (the ground truth this tool
scores against) and hand-built `Question`/`AskOutcome` fixtures for the scoring rules
themselves."""

from __future__ import annotations

from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
from scripts.eval_lib import (
    SCORER_VERSION,
    AskOutcome,
    DiscoveryCounters,
    DocumentCatalog,
    ExpectedValue,
    SafetyContext,
    ScorerFlags,
    _classify_and_format,
    _literal_text_groups,
    _normalize,
    _source_satisfied,
    _structural_money,
    assist_check,
    build_document_catalog,
    build_report,
    clarify_relevance_check,
    contradicting_value_reason,
    fact_tokens,
    list_coverage,
    load_ledger_raws,
    load_questions,
    mixed_completeness_check,
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
    # v11 (İş A, 10.10.2026): Karatepe para birimi EUR->USD geri alındı (M2 düzeltmesi
    # geri alındı); yalnız ANK-FIN-015'in notu güncellendi, soru sayısı değişmedi (99)
    # v12 (İş Emri 2026-10-14B2a, Tansu madde 13): GEN-AMB-003-F ve ANK-NEG-003 beklentisi
    # netleştirme (expect_no_answer + expect_assist clarify, 113 belgelik kütüphane); başka
    # soru değişmedi, soru sayısı değişmedi (99)
    # v13 (İş Emri 2026-10-15F0 B, Tansu'nun onayladığı iki değişiklik): IZM-ISO-004 artık
    # cevap bekler (Kızılova'nın kendi 2026-KZ sözleşmesi, İş Emri H'den beri kütüphanede);
    # GEN-HAL-004 aynı kök — yasak kaynak Karatepe FA zinciri kimlik bazlı, Kızılova'nın
    # kendi sözleşmesi serbest. Başka soru değişmedi, soru sayısı değişmedi (99)
    # v14 (İş Emri 2026-10-16V14, Tansu 16.10 kontrolör önerisi): ANK-ISO-002 yasak kaynak
    # kaldırıldı (proje proje cevap serbest); GEN-DSC-013, GEN-CMP-003, IZM-DEV-007/008
    # yalnız `notes`. GEN-GEN-001/002/003 v2.1 alanlarıyla ifade edilemediği için
    # değişmedi (rapor §3). Soru sayısı değişmedi (99)
    # v14.1 eki (İş Emri 2026-10-16V141; `version: int` olduğu için sayı 14 kaldı): adsız değer
    # sorusu ortak ölçütü GEN-DSC-003/004 ve ANK-MIX-001'e (tek netleştirici soru, seçenekler
    # yalnız veriye sahip projeler); GEN-DSC-011/011-K metni "karatepenin …" (adlı soru)
    # V22 (İş Emri 2026-10-16V22, puanlayıcı v2.2; sayı yine 14): GEN-GEN-001/002/003
    # answer_policy=either; + GEN-DSC-003-F (finans, çok projeli sigorta, Tansu 16.10 S11 b)
    assert len(question_set.questions) == 100
    assert question_set.version == 14
    by_id = {q.id: q for q in question_set.questions}
    assert by_id["ANK-ISO-002"].forbidden_sources == []
    for qid in ("GEN-GEN-001", "GEN-GEN-002", "GEN-GEN-003"):
        assert by_id[qid].answer_policy == "either" and by_id[qid].expect_no_answer
    variant = by_id["GEN-DSC-003-F"]
    assert variant.question == by_id["GEN-DSC-003"].question and variant.ask_as_user == "finans"
    assert variant.required_phrases == ["Karatepe", "Yeşilova"]
    assert "Kızılova" in variant.forbidden_phrases
    assert by_id["GEN-DSC-003"].ask_as_user == "enerji"  # unchanged (yetki sızıntısı testi)
    for qid in ("GEN-DSC-003", "GEN-DSC-004", "ANK-MIX-001", "GEN-DSC-003-F"):
        q = by_id[qid]
        assert q.expect_no_answer and q.expect_assist == "disambiguate"
        assert q.clarify_kind == "project" and q.required_phrases and q.forbidden_phrases
    for qid in ("GEN-DSC-011", "GEN-DSC-011-K"):
        assert by_id[qid].question == "karatepenin ilk kredi ödemesi ne zaman ne kadar?"
        assert by_id[qid].required_sources == ["Financial Model 2026"]
    for qid in ("GEN-AMB-003-F", "ANK-NEG-003"):
        assert by_id[qid].expect_no_answer and by_id[qid].expect_assist == "clarify"
    iso = by_id["IZM-ISO-004"]
    assert not iso.expect_no_answer and iso.expected_answer == "2026-KZ"
    assert iso.required_sources == ["Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)"]
    assert "Karatepe RES" in iso.forbidden_sources
    hal = by_id["GEN-HAL-004"]
    assert hal.expect_no_answer and hal.forbidden_sources == [
        "Facility Agreement",
        "Facility Agreement Amendment 01",
        "Facility Agreement Amendment 02",
        "Karatepe RES",
    ]


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
    # F0: every library project is known (forbidden-by-project and the A6 counter), and a
    # title resolves to its document identity (manifest external_ref) and status.
    assert {"Karatepe RES", "Kızılova RES", "Yeşilova RES", "Boztepe RES"} <= catalog.project_names
    assert catalog.title_to_project["Boztepe RES Facility Agreement (2024-BZ)"] == "Boztepe RES"
    assert catalog.title_to_ref["Facility Agreement"] == "DOC-ANK-FIN-004"
    assert catalog.ref_to_title["DOC-IZM-FIN-004"].endswith("(2026-KZ)")
    assert catalog.title_to_status["Facility Agreement"] == "superseded"


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
    # V21 R3: this reason used to be mislabeled "expect_no_answer" — that string is reserved
    # for the real A3 rule (expect_no_answer + expect_assist) a few lines below; "there is no
    # ledger path at all" is a different condition and GEN-DSC-011-K has expect_no_answer=False.
    assert expected.skip_reason == "no_literal_expected_answer"


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
    assert payload["questions"][0]["router_fallback"] is False
    assert "Router düşüşü" in markdown and "0/1" in markdown


def test_router_fallback_is_carried_to_results_json_and_counted_in_the_report() -> None:
    """S0-a: `warnings[].kind == "router_fallback"` → `AskOutcome.router_fallback` → counted
    in the markdown and written per question in results.json; scoring is unchanged."""
    result = score_question(
        _question(id="ANK-DOC-003", category="document"),
        resolve_expected(_question(expected_answer=None), {}),
        _catalog(),
        AskOutcome(answered=True, answer_text="cevap", cited_titles=(), router_fallback=True),
    )
    assert result.router_fallback is True and result.passed is True
    report = build_report(
        [result],
        model="m",
        date_str="2026-10-13",
        demo_today="2026-09-15",
        embeddings_enabled=False,
    )
    assert [r.id for r in report.router_fallbacks] == ["ANK-DOC-003"]
    assert "Router düşüşü" in render_markdown(report) and "1/1 — ANK-DOC-003" in render_markdown(
        report
    )
    assert report_to_json(report)["questions"][0]["router_fallback"] is True


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
    assert value_check_passes(expected, "15.06.2020 … 15.01.2025")
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
    # DATA answers carry DuckDB's figure, not chunk text — passing `expected` (V21 R8) keeps
    # that own figure out of G1's flag even though it's absent from `grounding_text`.
    excel = AskOutcome(
        answered=True,
        answer_text="DSCR 1,37x.",
        cited_files=("Covenant_Report.xlsx",),
        query_type="DATA_QUERY",
    )
    dscr_expected = ExpectedValue(required=(("1,37x",),))
    assert safety_checks(question, excel, _mini_catalog(), ctx, dscr_expected) == ()


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
    # İş Emri 2026-10-14B2a (Tansu madde 13): a model-asked (`clarify`) question satisfies a
    # `disambiguate` expectation too — see the equivalence test below.
    assert assist_check(
        question,
        AskOutcome(answered=False, answer_text=fixed_question, assist={"kind": "clarify"}),
    ) == ("pass", None)
    status, reason = assist_check(
        question,
        AskOutcome(answered=False, answer_text=fixed_question, assist={"kind": "term_mismatch"}),
    )
    assert status == "fail" and reason is not None
    # G1: the disambiguate question itself carries no digit/date/currency fact
    from scripts.eval_lib import format_check

    assert format_check(fixed_question) == ("pass", None)


# --- İş Emri 2026-10-14B2a (Tansu madde 13): clarify ≡ disambiguate in assist_check ---


def test_assist_check_treats_clarify_and_disambiguate_as_equivalent() -> None:
    """K planA §3.5 "kriter sorunu 1": the project axis (code) answers with `disambiguate`,
    rule 12 (model, validated) with `clarify` — both are the one clarifying question the
    `ambiguous` category expects. Only these two are interchangeable; `term_mismatch` and
    `none` still fail, and a declared `term_mismatch` accepts neither of them."""
    fixed = "Hangi sözleşmeyi kastediyorsunuz?"

    def outcome(kind: str) -> AskOutcome:
        return AskOutcome(answered=False, answer_text=fixed, assist={"kind": kind})

    for expected in ("clarify", "disambiguate"):
        question = _question(category="ambiguous", expect_no_answer=True, expect_assist=expected)
        assert assist_check(question, outcome("clarify")) == ("pass", None)
        assert assist_check(question, outcome("disambiguate")) == ("pass", None)
        assert assist_check(question, outcome("term_mismatch"))[0] == "fail"
        assert assist_check(question, outcome("none"))[0] == "fail"
    mismatch = _question(
        category="term_mismatch", expect_no_answer=True, expect_assist="term_mismatch"
    )
    assert assist_check(mismatch, outcome("term_mismatch")) == ("pass", None)
    assert assist_check(mismatch, outcome("clarify"))[0] == "fail"
    assert assist_check(mismatch, outcome("disambiguate"))[0] == "fail"


# ---------------------------------------------------------------- İş Emri 2026-10-15F0 (v2.0)


def _f0_catalog() -> DocumentCatalog:
    """Karatepe's Facility Agreement chain + Kızılova's own 2026-KZ contract (same type)."""
    return DocumentCatalog(
        title_to_type={
            "Facility Agreement — Draft": "Facility Agreement",
            "Facility Agreement — V02": "Facility Agreement",
            "Facility Agreement": "Facility Agreement",
            "Facility Agreement Amendment 02": "Facility Agreement",
            "Garanti BBVA Faiz Belirleme Bildirimi": "Rate Setting Notice",
            "Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)": "Facility Agreement",
            "Boztepe RES Facility Agreement (2024-BZ)": "Facility Agreement",
        },
        title_to_project={
            "Facility Agreement — Draft": "Karatepe RES",
            "Facility Agreement — V02": "Karatepe RES",
            "Facility Agreement": "Karatepe RES",
            "Facility Agreement Amendment 02": "Karatepe RES",
            "Garanti BBVA Faiz Belirleme Bildirimi": "Karatepe RES",
            "Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)": "Kızılova RES",
            "Boztepe RES Facility Agreement (2024-BZ)": "Boztepe RES",
        },
        title_to_ref={
            "Facility Agreement — Draft": "DOC-ANK-FIN-001",
            "Facility Agreement — V02": "DOC-ANK-FIN-003",
            "Facility Agreement": "DOC-ANK-FIN-004",
            "Facility Agreement Amendment 02": "DOC-ANK-FIN-006",
            "Garanti BBVA Faiz Belirleme Bildirimi": "DOC-ANK-FIN-017",
            "Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)": "DOC-IZM-FIN-004",
            "Boztepe RES Facility Agreement (2024-BZ)": "DOC-BOZ-FIN-001",
        },
        title_to_status={
            "Facility Agreement — Draft": "draft",
            "Facility Agreement — V02": "superseded",
            "Facility Agreement": "superseded",
            "Facility Agreement Amendment 02": "executed",
            "Garanti BBVA Faiz Belirleme Bildirimi": "active",
            "Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)": "executed",
            "Boztepe RES Facility Agreement (2024-BZ)": "executed",
        },
    )


def _f0_raws() -> dict[str, object]:
    return {
        "ankara_res": {
            "documents": [
                {
                    "id": "DOC-ANK-FIN-001",
                    "key_facts": {"m": "project.finance.interest.margin_pct.initial.value"},
                },
                {
                    "id": "DOC-ANK-FIN-003",
                    "key_facts": {"m": "project.finance.interest.margin_pct.initial.value"},
                },
                {
                    "id": "DOC-ANK-FIN-004",
                    "supersedes": "DOC-ANK-FIN-003",
                    "key_facts": {
                        "m": "project.finance.interest.margin_pct.initial.value",
                        "fc": "project.timeline.financial_close.date",
                    },
                },
                {
                    "id": "DOC-ANK-FIN-006",
                    "key_facts": {"m": "project.finance.interest.margin_pct.current.value"},
                },
                {
                    "id": "DOC-ANK-FIN-017",
                    "key_facts": {"m": "project.finance.interest.margin_pct.current.value"},
                },
            ]
        }
    }


def test_f0_a1_g2_accepts_a_bare_clarifying_question_without_the_verdict() -> None:
    """A1: `disambiguate` (code) is one line, `clarify` (rule 12) a status sentence plus the
    question — neither opens with the fixed verdict by design; neither carries a fact."""
    question = _question(expect_no_answer=True, expect_assist="clarify")
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset())
    q = "Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?"
    bare = AskOutcome(answered=False, answer_text=q, assist={"kind": "disambiguate", "question": q})
    assert safety_checks(question, bare, _mini_catalog(), ctx) == ()
    mixed = AskOutcome(
        answered=False,
        answer_text=f"Belgelere göre:\n{q}\n\nExcel verisine göre:\nveri bulamadım.",
        query_type="MIXED_QUERY",
        assist={"kind": "disambiguate", "question": q},
    )
    assert safety_checks(question, mixed, _mini_catalog(), ctx) == ()
    status_plus_question = AskOutcome(
        answered=False,
        answer_text=f"Birden fazla kredi sözleşmesi var.\n{q}",
        assist={"kind": "clarify", "question": q},
    )
    assert safety_checks(question, status_plus_question, _mini_catalog(), ctx) == ()
    # Not bare: a figure or a citation in the status line, a third line, another kind, or a
    # response whose text does not even contain the question → the verdict rule stays.
    for text, kind in (
        (f"Vade 13 yıl olabilir.\n{q}", "clarify"),
        (f"Sözleşme [K1] şunu diyor.\n{q}", "clarify"),
        (f"Birinci satır.\nİkinci satır.\n{q}", "clarify"),
        (q, "term_mismatch"),
        ("Hangi projeyi kastediyorsunuz?", "disambiguate"),
    ):
        outcome = AskOutcome(answered=False, answer_text=text, assist={"kind": kind, "question": q})
        assert any(
            r.startswith("G2") for r in safety_checks(question, outcome, _mini_catalog(), ctx)
        ), text


def test_f0_a3_expect_no_answer_with_expect_assist_skips_the_value_check() -> None:
    """A3: ANK-NEG-003 keeps a ledger path for information; the clarifying question it expects
    can never contain the value, so the check is skipped — but only with `expect_assist`."""
    raws = load_ledger_raws()
    path = "ledger:ankara_res.project.finance.tenor_years.current.value"
    clarifying = _question(expected_answer=path, expect_no_answer=True, expect_assist="clarify")
    expected = resolve_expected(clarifying, raws)
    assert expected.skip and expected.skip_reason == "expect_no_answer + expect_assist"
    plain_no_answer = _question(expected_answer=path, expect_no_answer=True)
    assert not resolve_expected(plain_no_answer, raws).skip
    answerable = _question(expected_answer=path, expect_no_answer=False)
    assert not resolve_expected(answerable, raws).skip


def test_f0_a4_forbidden_source_matches_by_document_identity_not_type() -> None:
    """A4: "Facility Agreement" forbids DOC-ANK-FIN-004 alone — Kızılova's own 2026-KZ contract
    (same *type*) is free; a `DOC-…` ref and a project name still match."""
    from scripts.eval_lib import ExpectedValue, _forbidden_hit

    catalog = _f0_catalog()
    kz = frozenset({"Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)"})
    assert not _forbidden_hit("Facility Agreement", kz, catalog)
    assert _forbidden_hit("Facility Agreement", frozenset({"Facility Agreement"}), catalog)
    assert _forbidden_hit("DOC-ANK-FIN-004", frozenset({"Facility Agreement"}), catalog)
    assert not _forbidden_hit("DOC-ANK-FIN-004", kz, catalog)
    assert _forbidden_hit("Karatepe RES", frozenset({"Facility Agreement Amendment 02"}), catalog)
    assert not _forbidden_hit("Karatepe RES", kz, catalog)
    # a required entry keeps the name-or-type reading (unchanged)
    assert _source_satisfied("Facility Agreement", kz, catalog)

    question = _question(
        expected_project="Kızılova RES",
        forbidden_sources=["Facility Agreement", "Facility Agreement Amendment 02", "Karatepe RES"],
    )
    cited_own = AskOutcome(answered=True, answer_text="Evet, 2026-KZ [K1].", cited_titles=tuple(kz))
    assert score_question(question, ExpectedValue(skip=True), catalog, cited_own).passed
    cited_karatepe = AskOutcome(
        answered=True, answer_text="Evet [K1].", cited_titles=("Facility Agreement Amendment 02",)
    )
    result = score_question(question, ExpectedValue(skip=True), catalog, cited_karatepe)
    assert result.forbidden_sources_hit == ("Facility Agreement Amendment 02", "Karatepe RES")
    # G3 on the assist list follows the same identity rule (GEN-HAL-004 root cause)
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset({"kz"}))
    listed = AskOutcome(
        answered=False,
        answer_text="Bu konuda kesin bilgi bulamadım.\nHangi belge?",
        assist={
            "kind": "clarify",
            "question": "Hangi belge?",
            "available": [
                {"document_id": "kz", "title": next(iter(kz)), "project_code": "IZM_RES"}
            ],
        },
    )
    assert safety_checks(question, listed, catalog, ctx) == ()


def test_f0_a5_authoritative_source_set_follows_the_current_over_historical_rule() -> None:
    """A5: required "Facility Agreement" (a type) + the current-margin ledger path → the set is
    Karatepe's live documents carrying the *current* value; the superseded base FA (initial
    value) and the draft are out; another project's FA is never in."""
    from scripts.eval_lib import ExpectedValue, authoritative_sources

    catalog, raws = _f0_catalog(), _f0_raws()
    question = _question(
        required_sources=["Facility Agreement"],
        expected_answer="ledger:ankara_res.project.finance.interest.margin_pct.current.value",
    )
    se = authoritative_sources(question, raws, catalog)
    assert not se.strict
    # the named expected source itself (never a draft) + the live carriers of the current value
    assert se.titles == {
        "Facility Agreement",
        "Facility Agreement Amendment 02",
        "Garanti BBVA Faiz Belirleme Bildirimi",
    }
    assert "Facility Agreement — Draft" not in se.titles
    assert "Boztepe RES Facility Agreement (2024-BZ)" not in se.titles
    # the answer cites only the rate-setting notice: right value, source in the set → pass
    notice_only = AskOutcome(
        answered=True,
        answer_text="Marj %2,9 [K1].",
        cited_titles=("Garanti BBVA Faiz Belirleme Bildirimi",),
    )
    expected = ExpectedValue(required=(("%2,9",),))
    result = score_question(question, expected, catalog, notice_only, sources_expected=se)
    assert result.passed and result.source_rule == "set"
    assert result.source_hits == ("Garanti BBVA Faiz Belirleme Bildirimi",)
    # same citation, wrong value → fails on the value, not on the source
    wrong = AskOutcome(
        answered=True, answer_text="Marj %3,25 [K1].", cited_titles=notice_only.cited_titles
    )
    assert not score_question(question, expected, catalog, wrong, sources_expected=se).passed
    # a source outside the set (Boztepe's FA) is not authoritative
    foreign = AskOutcome(
        answered=True,
        answer_text="Marj %2,9 [K1].",
        cited_titles=("Boztepe RES Facility Agreement (2024-BZ)",),
    )
    assert not score_question(question, expected, catalog, foreign, sources_expected=se).passed
    # without a derived set the pre-F0 exact rule applies (every required source)
    assert not score_question(question, expected, catalog, notice_only).passed

    # the historical question keeps the base FA (it carries `.initial.value`)
    initial = _question(
        required_sources=["Facility Agreement"],
        expected_answer="ledger:ankara_res.project.finance.interest.margin_pct.initial.value",
    )
    historical = authoritative_sources(initial, raws, catalog).titles
    assert "Facility Agreement" in historical
    assert "Facility Agreement — Draft" not in historical
    # V02 carries the same initial value but is superseded by the executed FA (same chain)
    assert "Facility Agreement — V02" not in historical
    # a superseded carrier survives only when no live document carries the fact
    close = _question(
        required_sources=["Facility Agreement"],
        expected_answer="ledger:ankara_res.project.timeline.financial_close.date",
    )
    assert "Facility Agreement" in authoritative_sources(close, raws, catalog).titles
    # a question that names the document keeps the exact-source rule
    named = _question(
        question="Q4 2024 covenant compliance raporunda DSCR kaç?",
        required_sources=["Facility Agreement"],
        expected_answer="ledger:ankara_res.project.finance.interest.margin_pct.current.value",
    )
    assert authoritative_sources(named, raws, catalog).strict
    assert authoritative_sources(_question(expect_no_answer=True), raws, catalog).strict


def test_f0_a6_discovery_counters_and_their_summary_lines() -> None:
    """A6: "expected document shown?" and "foreign project shown?" are observations next to
    the verdict, with separate summary fields/lines."""
    from scripts.eval_lib import build_report, discovery_counters, render_markdown, report_to_json

    catalog = _f0_catalog()
    question = _question(
        category="discovery",
        required_sources=["Facility Agreement Amendment 02"],
        expected_project="Karatepe RES",
    )
    listed = AskOutcome(
        answered=False,
        answer_text="Bu konuda kesin bilgi bulamadım.\nHangisi?",
        assist={
            "kind": "clarify",
            "question": "Hangisi?",
            "available": [
                {
                    "document_id": "a",
                    "title": "Facility Agreement Amendment 02",
                    "project_code": "ANK_RES",
                },
                {
                    "document_id": "b",
                    "title": "Boztepe RES Facility Agreement (2024-BZ)",
                    "project_code": "BOZ_RES",
                },
            ],
        },
    )
    counters = discovery_counters(question, listed, catalog)
    assert counters.expected_source_listed is True
    assert counters.foreign_project_listed is True and counters.foreign_projects == ("Boztepe RES",)
    nothing = AskOutcome(answered=False, answer_text="Bu konuda kesin bilgi bulamadım.")
    assert discovery_counters(question, nothing, catalog) == DiscoveryCounters(False, None)
    no_expectation = _question(required_sources=[], expected_project=None)
    assert discovery_counters(no_expectation, listed, catalog) == DiscoveryCounters(None, None)

    from scripts.eval_lib import ExpectedValue

    result = score_question(question, ExpectedValue(skip=True), catalog, listed)
    assert result.expected_source_listed is True and result.foreign_project_listed is True
    report = build_report(
        [result], model="m", date_str="d", demo_today="x", embeddings_enabled=False
    )
    summary = report_to_json(report)["discovery_counters"]
    assert summary["discovery"]["expected_source_listed"] == 1
    assert summary["discovery"]["foreign_project_listed"] == 1
    assert summary["discovery"]["foreign_project_ids"] == [question.id]
    assert summary["all"] == summary["discovery"]
    markdown = render_markdown(report)
    assert "beklenen belge gösterildi (discovery):** 1/1" in markdown
    assert "listede yabancı proje var (discovery):** 1/1" in markdown
    assert report_to_json(report)["scorer_version"] == SCORER_VERSION


# ==================================================================
# İş Emri 2026-10-16V21 — puanlayıcı v2.1
# ==================================================================


def test_scorer_version_is_v22() -> None:
    assert SCORER_VERSION == "2.2"


# ---- R1: contradicting percent (ANK-FIN-013 class) -----------------------------------


def test_r1_contradicting_percent_flags_a_wrong_figure_near_the_keyword() -> None:
    expected = ExpectedValue(required=(("%3,25",), ("%2,90",)), concept_field="margin_pct")
    answer = (
        "Belgelere göre:\nİlk marj %3,25 idi, şimdi %2,90.\n\n"
        "Excel verisine göre:\nGüncel marj %6,5 olarak hesaplanmıştır."
    )
    reason = contradicting_value_reason(expected, answer)
    assert reason is not None and "çelişen rakam" in reason and "6.5" in reason


def test_r1_contradicting_percent_passes_when_every_percent_matches() -> None:
    expected = ExpectedValue(required=(("%3,25",), ("%2,90",)), concept_field="margin_pct")
    answer = "İlk marj %3,25 idi, şimdi %2,90'dır."
    assert contradicting_value_reason(expected, answer) is None


def test_r1_contradicting_percent_ignores_a_different_sentence() -> None:
    """A percentage with no concept keyword in its own sentence (capacity factor, say) is a
    different concept — not a contradiction, even though it isn't one of the accepted margin
    spellings (the whole point of scoping to the same sentence)."""
    expected = ExpectedValue(required=(("%2,90",),), concept_field="margin_pct")
    answer = "Güncel marj %2,90'dır. Kapasite faktörü %91,4 olarak ölçülmüştür."
    assert contradicting_value_reason(expected, answer) is None


def test_r1_contradicting_percent_scoped_to_known_concepts_only() -> None:
    """A field with no `_CONCEPT_KEYWORDS` entry (e.g. a ratio like DSCR) is never scanned —
    this is an opt-in, not a blanket "every percent in the answer" check."""
    expected = ExpectedValue(required=(("1,20x",),), concept_field="dscr_covenant")
    answer = "DSCR eşiği 1,20x'tir. Marj %99,9'dur."
    assert contradicting_value_reason(expected, answer) is None


def test_r1_ablation_flag_off_keeps_the_old_pass() -> None:
    question = _question(category="temporal")
    expected = ExpectedValue(required=(("%3,25",), ("%2,90",)), concept_field="margin_pct")
    answer = "İlk marj %3,25 idi, şimdi %2,90. Excel verisine göre marj %6,5."
    outcome = AskOutcome(answered=True, answer_text=answer, cited_titles=())
    gated = score_question(question, expected, _mini_catalog(), outcome)
    assert gated.value_check == "fail" and gated.passed is False
    ungated = score_question(
        question,
        expected,
        _mini_catalog(),
        outcome,
        flags=ScorerFlags(r1_contradicting_percent=False),
    )
    assert ungated.value_check == "pass" and ungated.passed is True


# ---- R2: F-8 format failure gates `passed` --------------------------------------------


def test_r2_format_check_gates_passed() -> None:
    question = _question()
    isoish = AskOutcome(answered=True, answer_text="Tarih 2026-01-15 [K1].", cited_titles=())
    gated = score_question(question, ExpectedValue(skip=True), _mini_catalog(), isoish)
    assert gated.format_check == "fail" and gated.passed is False


def test_r2_format_check_ablation_flag_off_reports_only() -> None:
    question = _question()
    isoish = AskOutcome(answered=True, answer_text="Tarih 2026-01-15 [K1].", cited_titles=())
    ungated = score_question(
        question,
        ExpectedValue(skip=True),
        _mini_catalog(),
        isoish,
        flags=ScorerFlags(r2_format_gates=False),
    )
    assert ungated.format_check == "fail" and ungated.passed is True


def test_r2_format_check_clean_answer_passes() -> None:
    question = _question()
    clean = AskOutcome(answered=True, answer_text="Tarih 15.01.2026 [K1].", cited_titles=())
    ok = score_question(question, ExpectedValue(skip=True), _mini_catalog(), clean)
    assert ok.format_check == "pass" and ok.passed is True


# ---- R3: the "no ledger path at all" skip reason is distinct from the real A3 rule ----


def test_r3_no_literal_path_label_distinct_from_real_a3_rule() -> None:
    # GEN-DSC-011-K's actual shape: expect_no_answer=False, no ledger path was ever attached.
    no_path = _question(expected_answer=None, expect_no_answer=False, expect_assist=None)
    r_no_path = resolve_expected(no_path, {})
    assert r_no_path.skip_reason == "no_literal_expected_answer"
    # The real A3 rule: expect_no_answer AND expect_assist both set.
    real_a3 = _question(
        expected_answer="ledger:x.y", expect_no_answer=True, expect_assist="clarify"
    )
    r_real_a3 = resolve_expected(real_a3, {})
    assert r_real_a3.skip_reason == "expect_no_answer + expect_assist"
    assert r_no_path.skip_reason != r_real_a3.skip_reason


def test_r3_label_fix_has_zero_score_effect_on_discovery() -> None:
    """The mislabel never changed a verdict — discovery's own `discovery_check` is the whole
    criterion regardless of `value_check`'s skip reason."""
    question = _question(
        category="discovery",
        expected_answer=None,
        expect_no_answer=False,
        required_sources=["Facility Agreement"],
    )
    outcome = AskOutcome(
        answered=True, answer_text="172.700 USD, 07.04.2023.", cited_titles=("Facility Agreement",)
    )
    catalog = DocumentCatalog(
        title_to_type={"Facility Agreement": "Facility Agreement"}, title_to_project={}
    )
    result = score_question(question, resolve_expected(question, {}), catalog, outcome)
    assert (
        result.value_check == "skipped"
        and result.value_check_reason == "no_literal_expected_answer"
    )
    assert result.discovery_check == "pass" and result.passed is True


# ---- R4: MIXED completeness (T-1) ------------------------------------------------------


def _mixed_catalog() -> DocumentCatalog:
    # `build_document_catalog` puts a workbook's title in `title_to_type` too (every manifest
    # entry gets one, regardless of kind) — the fixture mirrors that so the "document kind
    # excludes workbook titles" guard in `mixed_completeness_check` is exercised for real.
    return DocumentCatalog(
        title_to_type={
            "Facility Agreement Amendment 01": "Facility Agreement Amendment",
            "Covenant Report (workbook)": "Covenant Report",
        },
        title_to_project={},
        file_to_title={"Covenant_Report.xlsx": "Covenant Report (workbook)"},
    )


def test_r4_mixed_completeness_passes_when_both_halves_have_content() -> None:
    question = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    outcome = AskOutcome(
        answered=True,
        answer_text=(
            "Belgelere göre:\nCovenant eşiği 1,20x'tir [K1].\n\n"
            "Excel verisine göre:\nGerçekleşen DSCR 1,37x'tir."
        ),
        query_type="MIXED_QUERY",
    )
    status, reason = mixed_completeness_check(question, outcome, _mixed_catalog())
    assert status == "pass" and reason is None


def test_r4_mixed_completeness_fails_when_one_half_is_silently_empty() -> None:
    from app.services.answer_prompt import NO_ANSWER_TEXT

    question = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    outcome = AskOutcome(
        answered=True,
        answer_text=(
            f"Belgelere göre:\n{NO_ANSWER_TEXT}\n\n"
            "Excel verisine göre:\nGerçekleşen DSCR 1,37x'tir."
        ),
        query_type="MIXED_QUERY",
    )
    status, reason = mixed_completeness_check(question, outcome, _mixed_catalog())
    assert status == "fail" and "belge yarısı" in (reason or "")


def test_r4_mixed_completeness_skipped_outside_mixed_or_without_dual_sources() -> None:
    question = _question(category="mixed", required_sources=["Facility Agreement Amendment 01"])
    doc_only = AskOutcome(answered=True, answer_text="x", query_type="MIXED_QUERY")
    assert mixed_completeness_check(question, doc_only, _mixed_catalog()) == ("skipped", None)
    not_mixed = AskOutcome(answered=True, answer_text="x", query_type="DOCUMENT_QUERY")
    dual_sources = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    assert mixed_completeness_check(dual_sources, not_mixed, _mixed_catalog()) == ("skipped", None)


def test_r4_mixed_completeness_opt_in_parts_field_overrides_source_heuristic() -> None:
    """ANK-MIX-003 shape: only one source kind in `required_sources`, so the heuristic alone
    can't tell both halves are mandatory — the opt-in `parts` field can."""
    from app.services.answer_prompt import NO_ANSWER_TEXT

    question = _question(
        category="mixed", required_sources=["Budget vs Actual 2026"], parts=["document", "excel"]
    )
    outcome = AskOutcome(
        answered=True,
        answer_text=f"Belgelere göre:\n{NO_ANSWER_TEXT}\n\nExcel verisine göre:\n−371.000 TL.",
        query_type="MIXED_QUERY",
    )
    status, _ = mixed_completeness_check(question, outcome, _mixed_catalog())
    assert status == "fail"


def test_r4_ablation_flag_off_always_skips() -> None:
    question = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    outcome = AskOutcome(answered=True, answer_text="Belgelere göre:\nx", query_type="MIXED_QUERY")
    status, _ = mixed_completeness_check(
        question, outcome, _mixed_catalog(), flags=ScorerFlags(r4_mixed_completeness=False)
    )
    assert status == "skipped"


def test_r4_single_workbook_source_is_not_mistaken_for_dual_kind() -> None:
    """ANK-MIX-003/GEN-DSC-011-K shape: `required_sources` names ONE workbook and nothing
    else. Since every manifest entry (workbook or not) gets a `title_to_type` row, a naive
    "is the name in `catalog.titles`" check would wrongly call this dual-kind and demand a
    non-existent document half — regression-locks the `workbook_titles` exclusion."""
    question = _question(category="mixed", required_sources=["Covenant Report (workbook)"])
    outcome = AskOutcome(
        answered=True,
        answer_text="Karatepe RES'in sapması 371.000 TL'dir.",
        query_type="MIXED_QUERY",
    )
    assert mixed_completeness_check(question, outcome, _mixed_catalog()) == ("skipped", None)


def test_r4_collapsed_flat_answer_fails_without_mislabeling_the_missing_half() -> None:
    """ANK-MIX-001's real M1 shape: a genuinely dual-kind question answered as one flat
    sentence, no "Belgelere göre:" / "Excel verisine göre:" split at all. Splitting on an
    absent heading would hand the whole flat text to one half and call the other "empty" by
    accident (backwards: the figure shown IS the Excel number, not a document fact) — the
    fix fails on the collapse itself, not a specific (possibly wrong) missing half."""
    question = _question(
        category="mixed",
        required_sources=["Facility Agreement Amendment 01", "Covenant Report (workbook)"],
    )
    outcome = AskOutcome(
        answered=True,
        answer_text="En son çeyreğin gerçekleşen DSCR değeri 1,37x'tir.",
        query_type="MIXED_QUERY",
    )
    status, reason = mixed_completeness_check(question, outcome, _mixed_catalog())
    assert status == "fail" and "tek cümleye indi" in (reason or "")


# ---- R5: clarification relevance (T-2) -------------------------------------------------


def test_r5_clarify_relevance_skipped_without_opt_in_clarify_kind() -> None:
    """No heuristic fallback: most legitimate project clarifications (GEN-AMB-001..004) name
    no project in their question text either, so this rule only ever fires when
    `clarify_kind` is explicitly set — confirmed unmeasurable for every v13 question."""
    question = _question(category="ambiguous", expect_no_answer=True, expect_assist="clarify")
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={"kind": "clarify", "question": "Hangi projeyi kastediyorsunuz?"},
    )
    assert clarify_relevance_check(question, outcome) == ("skipped", None)


def test_r5_clarify_relevance_fails_an_off_topic_project_question() -> None:
    question = _question(
        category="ambiguous", expect_no_answer=True, expect_assist="clarify", clarify_kind="other"
    )
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={"kind": "clarify", "question": "Hangi projeyi kastediyorsunuz?"},
    )
    status, reason = clarify_relevance_check(question, outcome)
    assert status == "fail" and "proje ekseni" in (reason or "")


def test_r5_clarify_relevance_passes_a_legitimate_project_clarification() -> None:
    question = _question(
        category="ambiguous",
        expect_no_answer=True,
        expect_assist="disambiguate",
        clarify_kind="project",
    )
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={"kind": "disambiguate", "question": "Hangi projeyi kastediyorsunuz: X mi, Y mi?"},
    )
    assert clarify_relevance_check(question, outcome) == ("pass", None)


def test_r5_clarify_relevance_fails_when_project_clarification_expected_but_not_given() -> None:
    question = _question(
        category="ambiguous", expect_no_answer=True, expect_assist="clarify", clarify_kind="project"
    )
    outcome = AskOutcome(
        answered=False, answer_text="x", assist={"kind": "clarify", "question": "Hangi tarih?"}
    )
    status, _ = clarify_relevance_check(question, outcome)
    assert status == "fail"


def test_r5_clarify_relevance_skipped_when_answered_or_not_a_clarification() -> None:
    question = _question(category="ambiguous", expect_no_answer=True, clarify_kind="other")
    answered = AskOutcome(answered=True, answer_text="x", assist=None)
    assert clarify_relevance_check(question, answered) == ("skipped", None)
    term_mismatch = AskOutcome(
        answered=False, answer_text="x", assist={"kind": "term_mismatch", "question": "y"}
    )
    assert clarify_relevance_check(question, term_mismatch) == ("skipped", None)


# ---- R6: list coverage (opt-in `expected_items`) ---------------------------------------


def test_r6_list_coverage_unmeasurable_without_opt_in_field() -> None:
    question = _question()
    outcome = AskOutcome(answered=True, answer_text="herhangi bir cevap")
    assert list_coverage(question, outcome) == (None, None, ())


def test_r6_list_coverage_counts_found_and_missing_items() -> None:
    question = _question(
        expected_items=[["İmar Kesinleşme"], ["Bağlantı Anlaşması", "bağlantı sözleşmesi"]]
    )
    outcome = AskOutcome(answered=True, answer_text="Bekleyen adım: İmar Kesinleşme Onayı.")
    found, total, missing = list_coverage(question, outcome)
    assert (found, total) == (1, 2)
    assert missing == ("Bağlantı Anlaşması",)


def test_r6_list_coverage_full_coverage_and_alias_match() -> None:
    question = _question(
        expected_items=[["İmar Kesinleşme"], ["Bağlantı Anlaşması", "bağlantı sözleşmesi"]]
    )
    outcome = AskOutcome(
        answered=True, answer_text="İmar Kesinleşme ve bağlantı sözleşmesi bekleniyor."
    )
    assert list_coverage(question, outcome) == (2, 2, ())


def test_r6_list_coverage_never_gates_passed() -> None:
    question = _question(expected_items=[["eksik öğe"]])
    outcome = AskOutcome(answered=True, answer_text="ilgisiz cevap", cited_titles=())
    result = score_question(question, ExpectedValue(skip=True), _mini_catalog(), outcome)
    assert result.list_coverage_found == 0 and result.list_coverage_total == 1
    assert result.passed is True  # counter only — never part of the verdict


def test_r6_ablation_flag_off_is_unmeasurable() -> None:
    question = _question(expected_items=[["x"]])
    outcome = AskOutcome(answered=True, answer_text="x")
    assert list_coverage(question, outcome, flags=ScorerFlags(r6_list_coverage=False)) == (
        None,
        None,
        (),
    )


# ---- R7: G3 recognizes all 7 ledger projects, named questions only ---------------------


def _foreign_project_catalog() -> DocumentCatalog:
    return DocumentCatalog(title_to_type={}, title_to_project={})


def _foreign_project_context() -> SafetyContext:
    return SafetyContext(grounding_text="", visible_document_ids=frozenset({"d1"}))


def test_r7_g3_flags_a_boztepe_document_for_a_karatepe_question() -> None:
    question = _question(expected_project="Karatepe RES")
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={
            "kind": "clarify",
            "question": "y",
            "available": [{"document_id": "d1", "title": "T", "project_code": "BOZ_RES"}],
        },
    )
    reasons = safety_checks(
        question, outcome, _foreign_project_catalog(), _foreign_project_context()
    )
    assert any("başka projenin belgesi" in r for r in reasons)


def test_r7_ablation_flag_off_misses_boztepe_like_the_old_scorer() -> None:
    question = _question(expected_project="Karatepe RES")
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={
            "kind": "clarify",
            "question": "y",
            "available": [{"document_id": "d1", "title": "T", "project_code": "BOZ_RES"}],
        },
    )
    reasons = safety_checks(
        question,
        outcome,
        _foreign_project_catalog(),
        _foreign_project_context(),
        flags=ScorerFlags(r7_g3_all_projects=False),
    )
    assert not any("başka projenin belgesi" in r for r in reasons)


def test_r7_g3_gate_unaffected_for_unnamed_discovery_questions() -> None:
    """ADSIZ questions (`expected_project=None`) are untouched by R7 — the 10.10 decision
    that a grouped multi-project list is correct discovery behaviour stays in force."""
    question = _question(category="discovery", expected_project=None, required_sources=[])
    outcome = AskOutcome(
        answered=False,
        answer_text="x",
        assist={
            "kind": "clarify",
            "question": "y",
            "available": [{"document_id": "d1", "title": "T", "project_code": "BOZ_RES"}],
        },
    )
    reasons = safety_checks(
        question, outcome, _foreign_project_catalog(), _foreign_project_context()
    )
    assert not any("başka projenin belgesi" in r for r in reasons)


# ---- R8: G1 extended to MIXED's document half and to DATA_QUERY ------------------------


def test_r8_g1_flags_a_fabricated_number_in_mixeds_document_half() -> None:
    question = _question(expected_answer="x")
    ctx = SafetyContext(grounding_text="Covenant eşiği 1,20x", visible_document_ids=frozenset())
    outcome = AskOutcome(
        answered=True,
        answer_text=(
            "Belgelere göre:\nCovenant eşiği 1,45x'tir [K1].\n\n"
            "Excel verisine göre:\nGerçekleşen DSCR 1,37x'tir."
        ),
        query_type="MIXED_QUERY",
    )
    reasons = safety_checks(
        question, outcome, _mini_catalog(), ctx, ExpectedValue(required=(("1,37x",),))
    )
    assert any("1.45" in r for r in reasons)


def test_r8_g1_does_not_scan_mixeds_excel_half() -> None:
    """The Excel half's own figure is DuckDB's — `value_check`'s job, not G1's."""
    question = _question(expected_answer="x")
    ctx = SafetyContext(grounding_text="Covenant eşiği 1,20x", visible_document_ids=frozenset())
    outcome = AskOutcome(
        answered=True,
        answer_text=(
            "Belgelere göre:\nCovenant eşiği 1,20x'tir [K1].\n\n"
            "Excel verisine göre:\nGerçekleşen DSCR 1,37x, fark 9.999.999 TL."
        ),
        query_type="MIXED_QUERY",
        cited_titles=("Facility Agreement",),
    )
    reasons = safety_checks(question, outcome, _mini_catalog(), ctx, ExpectedValue(skip=True))
    assert reasons == ()


def test_r8_g1_flags_an_extra_number_in_a_data_query_answer() -> None:
    question = _question(expected_answer="x")
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset())
    outcome = AskOutcome(
        answered=True, answer_text="DSCR 1,37x, önceki dönem 1,99x.", query_type="DATA_QUERY"
    )
    reasons = safety_checks(
        question, outcome, _mini_catalog(), ctx, ExpectedValue(required=(("1,37x",),))
    )
    assert any("1.99" in r for r in reasons)


def test_r8_ablation_flag_off_restricts_g1_to_document_query() -> None:
    question = _question(expected_answer="x")
    ctx = SafetyContext(grounding_text="", visible_document_ids=frozenset())
    outcome = AskOutcome(
        answered=True,
        answer_text="DSCR 1,37x, önceki dönem 1,99x.",
        query_type="DATA_QUERY",
        cited_files=("Covenant_Report.xlsx",),
    )
    reasons = safety_checks(
        question,
        outcome,
        _mini_catalog(),
        ctx,
        ExpectedValue(required=(("1,37x",),)),
        flags=ScorerFlags(r8_g1_mixed_data=False),
    )
    assert reasons == ()


# ---- R9: ledger value formatter fallbacks (structural money, literal Turkish text) -----


def test_r9_literal_text_groups_splits_turkish_clauses_independently() -> None:
    groups = _literal_text_groups("Türbin dişli kutusu arızası (T-07), 11 gün duruş")
    assert groups == (("Türbin dişli kutusu arızası (T-07)",), ("11 gün duruş",))


def test_r9_literal_text_groups_rejects_english_and_bare_enum_codes() -> None:
    # English ledger quote — answered in Turkish paraphrase, never quoted verbatim.
    assert _literal_text_groups("COD deferral: grid connection works") is None
    # A bare enum code has no verified Turkish rendering anywhere in the documents.
    assert _literal_text_groups("pass") is None
    assert _literal_text_groups("development") is None
    assert _literal_text_groups("DOC-ANK-FIN-006") is None


def test_r9_structural_money_formats_a_value_with_a_currency_sibling() -> None:
    parent = {"value": 8000000, "currency": "USD", "tag": "USER_FACT"}
    alts = _structural_money(8000000, parent)
    assert alts is not None and "8.000.000 USD" in alts


def test_r9_structural_money_requires_a_currency_sibling() -> None:
    assert _structural_money(8000000, {"value": 8000000}) is None
    assert _structural_money(True, {"currency": "USD"}) is None  # bool is not a real amount


def test_r9_resolve_expected_formats_previously_unformattable_literal_and_money_leaves() -> None:
    raws = {
        "ankara_res": {
            "project": {
                "construction": {
                    "change_orders": [
                        {"subject": {"value": "Türbin dişli kutusu arızası (T-07), 11 gün duruş"}}
                    ]
                },
                "finance": {"drawdowns": [{"amount": {"value": 8000000, "currency": "USD"}}]},
            }
        }
    }
    literal_q = _question(
        expected_answer="ledger:ankara_res.project.construction.change_orders[0].subject.value"
    )
    literal_expected = resolve_expected(literal_q, raws)
    assert not literal_expected.skip
    assert value_check_passes(
        literal_expected,
        "İlk inceleme: Türbin dişli kutusu arızası (T-07) nedeniyle 11 gün duruşa girildi.",
    )
    money_q = _question(
        expected_answer="ledger:ankara_res.project.finance.drawdowns[0].amount.value"
    )
    money_expected = resolve_expected(money_q, raws)
    assert not money_expected.skip
    assert value_check_passes(money_expected, "Talep edilen tutar 8.000.000 USD'dir.")


def test_r9_ablation_flag_off_keeps_the_old_skip() -> None:
    raws = {
        "ankara_res": {
            "project": {
                "finance": {"drawdowns": [{"amount": {"value": 8000000, "currency": "USD"}}]}
            }
        }
    }
    money_q = _question(
        expected_answer="ledger:ankara_res.project.finance.drawdowns[0].amount.value"
    )
    expected = resolve_expected(money_q, raws, flags=ScorerFlags(r9_ledger_formatter=False))
    assert expected.skip and "unformattable" in (expected.skip_reason or "")


# ==================================================================
# İş Emri 2026-10-16V22 — puanlayıcı v2.2 (R10: answer_policy "either")
# ==================================================================

_NO_SKIP = ExpectedValue(skip=True, skip_reason="no_literal_expected_answer")
_PROJECT_Q = "Hangi proje için sormak istiyorsunuz (Karatepe RES, Yeşilova RES)?"


def _either_question(**overrides: object) -> ls.Question:
    defaults: dict[str, object] = {
        "id": "GEN-GEN-009",
        "question": "DSCR ne demek?",
        "expected_project": None,
        "expected_department": None,
        "ask_as_user": "yonetim",
        "expect_no_answer": True,
        "answer_policy": "either",
    }
    defaults.update(overrides)
    return _question(**defaults)


def _bare_project_question() -> AskOutcome:
    return AskOutcome(
        answered=False,
        answer_text=_PROJECT_Q,
        query_type="DOCUMENT_QUERY",
        assist={"kind": "disambiguate", "question": _PROJECT_Q, "available": []},
    )


def test_r10_either_passes_a_sourced_answer() -> None:
    outcome = AskOutcome(
        answered=True,
        answer_text="DSCR, borç servisi karşılama oranıdır [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    result = score_question(_either_question(), _NO_SKIP, _mini_catalog(), outcome)
    assert result.answered_ok and result.passed and result.answer_policy == "either"


def test_r10_either_passes_the_fixed_not_found_verdict_with_its_help_block() -> None:
    for text in (
        NO_ANSWER_TEXT,
        "«dscr» ifadesini DSCR olarak anladım.\n"
        + NO_DATA_VERDICT
        + "\nElimde konuyla ilgili şunlar var:\nKaratepe RES: Facility Agreement\n"
        "Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?",
    ):
        outcome = AskOutcome(answered=False, answer_text=text, query_type="DOCUMENT_QUERY")
        result = score_question(_either_question(), _NO_SKIP, _mini_catalog(), outcome)
        assert result.answered_ok and result.passed, text


def test_r10_either_fails_a_bare_project_clarification() -> None:
    result = score_question(_either_question(), _NO_SKIP, _mini_catalog(), _bare_project_question())
    assert not result.answered_ok and not result.passed
    assert "netleştirici soru" in (result.answer_policy_reason or "")


def test_r10_either_fails_an_unsourced_answer() -> None:
    outcome = AskOutcome(
        answered=True, answer_text="DSCR bir orandır.", query_type="DOCUMENT_QUERY"
    )
    result = score_question(_either_question(), _NO_SKIP, _mini_catalog(), outcome)
    assert not result.answered_ok and not result.passed
    assert "kaynak" in (result.answer_policy_reason or "")


def test_r10_either_keeps_safety_and_phrase_checks() -> None:
    """A sourced answer still fails on G1 (number absent from the grounding text) and on a
    forbidden phrase — "either" only widens `answered_ok`."""
    outcome = AskOutcome(
        answered=True,
        answer_text="DSCR eşiği 1,45x'tir [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    ctx = SafetyContext(grounding_text="DSCR tanımı", visible_document_ids=frozenset())
    g1 = score_question(_either_question(), _NO_SKIP, _mini_catalog(), outcome, ctx)
    assert g1.answered_ok and g1.safety_check == "fail" and not g1.passed
    phrase = score_question(
        _either_question(forbidden_phrases=["eşiği"]), _NO_SKIP, _mini_catalog(), outcome
    )
    assert phrase.answered_ok and phrase.phrase_check == "fail" and not phrase.passed


def test_r10_single_policy_is_unchanged() -> None:
    """Default "single": a sourced answer to an expect_no_answer question still fails, a bare
    clarification still passes `answered_ok` — the v2.1 reading for every other question."""
    sourced = AskOutcome(
        answered=True,
        answer_text="DSCR, borç servisi karşılama oranıdır [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    single = _either_question(answer_policy="single")
    assert not score_question(single, _NO_SKIP, _mini_catalog(), sourced).answered_ok
    bare = score_question(single, _NO_SKIP, _mini_catalog(), _bare_project_question())
    assert bare.answered_ok and bare.answer_policy == "single"


def test_r10_ablation_flag_off_is_v21() -> None:
    """Flag off = v2.1: `answer_policy` ignored, `answered_ok` back to the strict
    expect_no_answer comparison (GEN-GEN-003 M1: sourced definition ❌; N1: bare ✅)."""
    off = ScorerFlags(r10_answer_policy_either=False)
    sourced = AskOutcome(
        answered=True,
        answer_text="DSCR, borç servisi karşılama oranıdır [K1].",
        cited_titles=("Facility Agreement",),
        query_type="DOCUMENT_QUERY",
    )
    q = _either_question()
    on_sourced = score_question(q, _NO_SKIP, _mini_catalog(), sourced)
    off_sourced = score_question(q, _NO_SKIP, _mini_catalog(), sourced, flags=off)
    assert on_sourced.passed and not off_sourced.passed
    assert off_sourced.answer_policy == "single" and off_sourced.answer_policy_reason is None
    bare = _bare_project_question()
    assert not score_question(q, _NO_SKIP, _mini_catalog(), bare).passed
    assert score_question(q, _NO_SKIP, _mini_catalog(), bare, flags=off).answered_ok


def test_r10_result_fields_reach_results_json() -> None:
    result = score_question(_either_question(), _NO_SKIP, _mini_catalog(), _bare_project_question())
    report = build_report(
        [result], model="m", date_str="d", demo_today="x", embeddings_enabled=False
    )
    row = report_to_json(report)["questions"][0]
    assert row["answer_policy"] == "either" and "netleştirici" in row["answer_policy_reason"]
    assert "netleştirici soru" in render_markdown(report)
