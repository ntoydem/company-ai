"""Truth-ledger validator (Phase 2.1). Rule tests copy the master ledger to a temp dir and
break ONE thing with a throwaway value, then assert the rule code fires — no demo figure
is asserted here, only that the validator sees what it must see."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from seed_data.generator import ledger_schema as ls
from seed_data.generator import validate_ledger as vl


def _run(master: Path, questions: Path | None = None) -> vl.Report:
    report, _ = vl.validate(master, questions)
    return report


def _codes(report: vl.Report) -> list[str]:
    return [issue.render() for issue in report.issues if issue.level == "ERROR"]


def _mutated(tmp_path: Path, file: str, mutate: Callable[[dict[str, Any]], None]) -> Path:
    master = tmp_path / "master"
    shutil.copytree(vl.DEFAULT_MASTER, master)
    path = master / file
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return master


def _mutated_questions(tmp_path: Path, mutate: Callable[[dict[str, Any]], None]) -> Path:
    data = json.loads(vl.DEFAULT_QUESTIONS.read_text(encoding="utf-8"))
    mutate(data)
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _has(report: vl.Report, code: str) -> bool:
    return any(code in line for line in _codes(report))


# --- kabul kriteri: validator 0 hata -------------------------------------------------


def test_master_ledger_validates_clean() -> None:
    report = _run(vl.DEFAULT_MASTER, vl.DEFAULT_QUESTIONS)
    assert _codes(report) == []


def test_master_ledger_carries_tags() -> None:
    """Approved values are USER_FACT (ledger onayı, 23.09.2026); anything added later
    starts as AI_ASSUMPTION — both are counted, neither is forbidden."""
    _, tags = vl.validate(vl.DEFAULT_MASTER, None)
    assert tags["USER_FACT"] + tags["AI_ASSUMPTION"] > 0


# --- kabul kriteri: Ankara zinciri --------------------------------------------------


def test_facility_chain_is_linear_and_complete(tmp_path: Path) -> None:
    def break_version(data: dict[str, Any]) -> None:
        chain = data["project"]["finance"]["facility_chain"]
        doc = next(d for d in data["documents"] if d["id"] == chain[-1])
        doc["version"] = "AMD09"

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", break_version)), "F6")


def test_facility_chain_must_have_single_current_link(tmp_path: Path) -> None:
    def two_current(data: dict[str, Any]) -> None:
        chain = data["project"]["finance"]["facility_chain"]
        doc = next(d for d in data["documents"] if d["id"] == chain[0])
        doc["status"] = "active"

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", two_current)), "F6")


# --- kabul kriteri: 3. işletme yılı DEMO_TODAY'e göre --------------------------------


def test_operating_year_is_anniversary_based() -> None:
    today = date(2030, 6, 1)
    assert vl.operating_year(today, date(2030, 6, 1)) == 1
    assert vl.operating_year(today, date(2029, 6, 2)) == 1
    assert vl.operating_year(today, date(2029, 5, 31)) == 2
    assert vl.operating_year(today, date(2027, 6, 2)) == 3
    assert vl.operating_year(today, date(2027, 5, 30)) == 4


def test_cod_outside_third_year_window_is_error(tmp_path: Path) -> None:
    def move_cod(data: dict[str, Any]) -> None:
        timeline = data["project"]["timeline"]
        cod = timeline["cod_actual"]["date"]
        moved = date(cod.year - 3, cod.month, cod.day)
        timeline["cod_actual"]["date"] = moved
        timeline["operation_start"]["date"] = moved

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", move_cod)), "C6")


# --- kabul kriteri: İzmir lisans sonrası alanlar null --------------------------------


def test_izmir_post_licence_fields_must_be_null(tmp_path: Path) -> None:
    def fill_licence(data: dict[str, Any]) -> None:
        data["project"]["timeline"]["licence"] = {
            "date": date(2030, 1, 1),
            "doc": None,
            "tag": "AI_ASSUMPTION",
        }

    assert _has(_run(_mutated(tmp_path, "izmir_res.yaml", fill_licence)), "I1")


def test_izmir_cannot_carry_finance_documents(tmp_path: Path) -> None:
    def add_finance_doc(data: dict[str, Any]) -> None:
        data["documents"][0]["type"] = "Facility Agreement"

    assert _has(_run(_mutated(tmp_path, "izmir_res.yaml", add_finance_doc)), "I2")


# --- kabul kriteri: her tutarda para birimi ------------------------------------------


def test_money_without_currency_is_error(tmp_path: Path) -> None:
    def drop_currency(data: dict[str, Any]) -> None:
        del data["project"]["finance"]["capex"]["currency"]

    report = _run(_mutated(tmp_path, "ankara_res.yaml", drop_currency))
    assert any("project.finance.capex.currency" in line for line in _codes(report))


def test_missing_tag_is_error(tmp_path: Path) -> None:
    def drop_tag(data: dict[str, Any]) -> None:
        del data["project"]["capacity_mw"]["current"]["tag"]

    report = _run(_mutated(tmp_path, "ankara_res.yaml", drop_tag))
    assert any("project.capacity_mw.current.tag" in line for line in _codes(report))


# --- kabul kriteri: soru kotaları ----------------------------------------------------


def test_question_quotas(tmp_path: Path) -> None:
    def drop_authorization(data: dict[str, Any]) -> None:
        data["questions"] = [q for q in data["questions"] if q["category"] != "authorization"]

    report = _run(vl.DEFAULT_MASTER, _mutated_questions(tmp_path, drop_authorization))
    assert _has(report, "Q2: authorization")


def test_question_ledger_reference_must_resolve(tmp_path: Path) -> None:
    def bad_ref(data: dict[str, Any]) -> None:
        data["questions"][0]["expected_answer"] = "ledger:ankara_res.project.no_such_key"

    assert _has(_run(vl.DEFAULT_MASTER, _mutated_questions(tmp_path, bad_ref)), "Q4")


def test_authorization_question_must_be_asked_as_enerji(tmp_path: Path) -> None:
    def wrong_user(data: dict[str, Any]) -> None:
        q = next(q for q in data["questions"] if q["category"] == "authorization")
        q["ask_as_user"] = "finans"

    assert _has(_run(vl.DEFAULT_MASTER, _mutated_questions(tmp_path, wrong_user)), "Q3")


# --- kapsam: kronoloji, finans, isim, slug -------------------------------------------


def test_chronology_rules(tmp_path: Path) -> None:
    def close_before_signing(data: dict[str, Any]) -> None:
        timeline = data["project"]["timeline"]
        signed = timeline["financing_signed"]["date"]
        timeline["financial_close"]["date"] = date(signed.year - 1, signed.month, signed.day)

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", close_before_signing)), "C1")


def test_finance_sums(tmp_path: Path) -> None:
    def break_split(data: dict[str, Any]) -> None:
        data["project"]["finance"]["local_debt"]["value"] += 1

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", break_split)), "F1")


def test_covenant_result_must_match_threshold(tmp_path: Path) -> None:
    def flip_result(data: dict[str, Any]) -> None:
        test = data["project"]["finance"]["covenant_tests"][0]
        test["result"] = "fail" if test["result"] == "pass" else "pass"

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", flip_result)), "F5")


def test_name_whitelist_regex(tmp_path: Path) -> None:
    def real_looking_name(data: dict[str, Any]) -> None:
        data["documents"][0]["parties"].append("Gerçek Bir Şirket A.Ş.")

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", real_looking_name)), "N1")


def test_department_slug_known(tmp_path: Path) -> None:
    def english_slug(data: dict[str, Any]) -> None:
        data["documents"][0]["department"] = "finance"

    report = _run(_mutated(tmp_path, "ankara_res.yaml", english_slug))
    assert any("documents.0.department" in line for line in _codes(report))


def test_cross_project_reference_is_error(tmp_path: Path) -> None:
    def leak(data: dict[str, Any]) -> None:
        data["documents"][0]["key_facts"]["leak"] = "ankara_res.project.finance.capex.value"

    assert _has(_run(_mutated(tmp_path, "izmir_res.yaml", leak)), "I3")


def test_demo_today_must_agree_across_files(tmp_path: Path) -> None:
    def shift(data: dict[str, Any]) -> None:
        data["meta"]["demo_today"] = date(2031, 1, 1)

    assert _has(_run(_mutated(tmp_path, "fx_rates.yaml", shift)), "C10")


def test_expiration_date_must_be_after_effective_date(tmp_path: Path) -> None:
    """ADR-026: an expiration before the document even starts is nonsensical."""

    def before_effective(data: dict[str, Any]) -> None:
        doc = data["documents"][0]
        doc["expiration_date"] = {"value": date(2020, 6, 14), "tag": "AI_ASSUMPTION"}

    assert _has(_run(_mutated(tmp_path, "ankara_res.yaml", before_effective)), "C11")


def test_resolve_path_supports_negative_index() -> None:
    root = {"a": {"b": [{"c": 1}, {"c": 2}]}}
    assert vl.resolve_path(root, "a.b[-1].c") == 2
    assert vl.resolve_path(root, "a.b[0].c") == 1


def test_comparison_questions_need_two_facts_no_project_and_forbidden_phrases(
    tmp_path: Path,
) -> None:
    def single_fact(data: dict[str, Any]) -> None:
        q = next(q for q in data["questions"] if q["category"] == "comparison")
        q["expected_answer"] = q["expected_answer"][0]

    def with_project(data: dict[str, Any]) -> None:
        q = next(q for q in data["questions"] if q["category"] == "comparison")
        q["expected_project"] = "Karatepe RES"

    def no_phrases(data: dict[str, Any]) -> None:
        q = next(q for q in data["questions"] if q["category"] == "comparison")
        q["forbidden_phrases"] = []

    for mutate in (single_fact, with_project, no_phrases):
        assert _has(_run(vl.DEFAULT_MASTER, _mutated_questions(tmp_path, mutate)), "Q6")


def test_list_expected_answer_paths_are_each_checked(tmp_path: Path) -> None:
    def bad_second(data: dict[str, Any]) -> None:
        q = next(q for q in data["questions"] if q["category"] == "comparison")
        q["expected_answer"][1] = "ledger:izmir_res.project.no_such_key"

    assert _has(_run(vl.DEFAULT_MASTER, _mutated_questions(tmp_path, bad_second)), "Q4")


# --- kapsam: kasıtlı çelişki grupları (Adım 5, C1) -----------------------------------


def test_find_conflict_groups_walks_nested_dicts_and_lists() -> None:
    """Pure function, no file I/O: `conflict_group` is found at any depth, in a dict
    nested under a list, and the path/deliberate_conflict/conflict_kind for each hit is
    recorded."""
    node = {
        "a": {
            "value": 1,
            "conflict_group": "g1",
            "deliberate_conflict": True,
            "conflict_kind": "genuine_conflict",
        },
        "b": [
            {
                "value": 2,
                "conflict_group": "g1",
                "deliberate_conflict": True,
                "conflict_kind": "genuine_conflict",
            },
            {"value": 3, "conflict_group": "g2"},  # no deliberate_conflict/conflict_kind at all
        ],
        "c": {"nested": {"value": 4}},  # no conflict_group anywhere here
    }
    groups = vl.find_conflict_groups(node, "x.yaml")
    assert groups["g1"] == [
        ("x.yaml", "a", True, "genuine_conflict"),
        ("x.yaml", "b[0]", True, "genuine_conflict"),
    ]
    assert groups["g2"] == [("x.yaml", "b[1]", False, None)]
    assert "g3" not in groups


def test_find_conflict_groups_empty_for_a_tree_without_any_tag() -> None:
    assert vl.find_conflict_groups({"a": {"value": 1}, "b": [1, 2]}, "x.yaml") == {}


def test_conflict_group_can_span_two_different_files() -> None:
    """`check_conflict_groups` aggregates across every raw file, not just one — a group's
    two members don't have to live in the same ledger."""
    raws = {
        "ankara_res": {
            "fact": {
                "value": 1,
                "conflict_group": "g",
                "deliberate_conflict": True,
                "conflict_kind": "genuine_conflict",
            }
        },
        "izmir_res": {
            "fact": {
                "value": 2,
                "conflict_group": "g",
                "deliberate_conflict": True,
                "conflict_kind": "genuine_conflict",
            }
        },
    }
    report = vl.Report()
    vl.check_conflict_groups(raws, report)
    assert _codes(report) == []


def test_conflict_group_with_only_one_member_is_an_error(tmp_path: Path) -> None:
    def untag_one_member(data: dict[str, Any]) -> None:
        del data["project"]["finance"]["contract_amount"]["conflict_group"]
        del data["project"]["finance"]["contract_amount"]["deliberate_conflict"]

    report = _run(_mutated(tmp_path, "ankara_res.yaml", untag_one_member))
    assert _has(report, "C1")
    assert any("only one member" in line for line in _codes(report))


def test_conflict_group_member_missing_deliberate_conflict_flag_is_an_error(
    tmp_path: Path,
) -> None:
    def unflag_one_member(data: dict[str, Any]) -> None:
        data["project"]["finance"]["total_debt"]["deliberate_conflict"] = False

    report = _run(_mutated(tmp_path, "ankara_res.yaml", unflag_one_member))
    assert _has(report, "C1")
    assert any("missing deliberate_conflict" in line for line in _codes(report))


def test_conflict_group_name_typo_still_reads_as_two_singleton_groups(
    tmp_path: Path,
) -> None:
    """A typo'd `conflict_group` on one of the two real members splits the pair into two
    groups of one each — both must fire, not just one."""

    def typo_group_name(data: dict[str, Any]) -> None:
        data["project"]["finance"]["total_debt"]["conflict_group"] = "karatepe-kredi-tutarii"

    report = _run(_mutated(tmp_path, "ankara_res.yaml", typo_group_name))
    codes = _codes(report)
    assert sum("only one member" in line for line in codes) == 2


def test_conflict_group_missing_conflict_kind_on_every_member_is_an_error(
    tmp_path: Path,
) -> None:
    """Both members lack `conflict_kind` (nobody tagged the trap's kind at all) — a
    distinct case from one member disagreeing with the other (see the mismatch test
    below), which the same group-of-None value would otherwise mask."""

    def drop_conflict_kind_from_both(data: dict[str, Any]) -> None:
        del data["project"]["finance"]["contract_amount"]["conflict_kind"]
        del data["project"]["finance"]["total_debt"]["conflict_kind"]

    report = _run(_mutated(tmp_path, "ankara_res.yaml", drop_conflict_kind_from_both))
    assert _has(report, "C1")
    assert any("missing conflict_kind" in line for line in _codes(report))


def test_conflict_group_member_missing_conflict_kind_reads_as_a_mismatch(
    tmp_path: Path,
) -> None:
    """Only one member drops `conflict_kind` while the other keeps `genuine_conflict` —
    None vs. a real value is itself a disagreement, so this is a mismatch, not the
    "nobody tagged it" case above."""

    def drop_conflict_kind_from_one(data: dict[str, Any]) -> None:
        del data["project"]["finance"]["total_debt"]["conflict_kind"]

    report = _run(_mutated(tmp_path, "ankara_res.yaml", drop_conflict_kind_from_one))
    assert _has(report, "C1")
    assert any("mismatched conflict_kind" in line for line in _codes(report))


def test_conflict_group_member_mismatched_conflict_kind_is_an_error(tmp_path: Path) -> None:
    def change_one_members_kind(data: dict[str, Any]) -> None:
        data["project"]["finance"]["total_debt"]["conflict_kind"] = "duplicate"

    report = _run(_mutated(tmp_path, "ankara_res.yaml", change_one_members_kind))
    assert _has(report, "C1")
    assert any("mismatched conflict_kind" in line for line in _codes(report))


# --- kapsam: Adım 5 Aşama C — PROJECT_PREFIX / company.yaml spv registry sync ---------


def test_project_prefix_matches_company_spv_registry() -> None:
    """`PROJECT_PREFIX`/`LEDGER_FILES`/`PROJECT_CODE_TO_RAW_KEY` are maintained by hand
    (Aşama B SORU 3 — not derived from `company.yaml`); this is the guard that keeps them
    from silently drifting apart from the one real source of truth, `company.yaml`'s own
    `spvs` registry."""
    raws = {
        name: yaml.safe_load((vl.DEFAULT_MASTER / filename).read_text(encoding="utf-8"))
        for name, filename in vl.LEDGER_FILES.items()
    }
    company = ls.CompanyLedger.model_validate(raws["company"])
    registry_codes = {spv.project_code for spv in company.spvs}
    assert registry_codes == set(vl.PROJECT_CODE_TO_RAW_KEY)
    for code, raw_key in vl.PROJECT_CODE_TO_RAW_KEY.items():
        assert raw_key in vl.LEDGER_FILES, f"{code}: {raw_key!r} missing from LEDGER_FILES"
        assert raw_key in vl.PROJECT_PREFIX, f"{code}: {raw_key!r} missing from PROJECT_PREFIX"
        assert code.startswith(vl.PROJECT_PREFIX[raw_key] + "_"), (
            f"{code}: PROJECT_PREFIX[{raw_key!r}] = {vl.PROJECT_PREFIX[raw_key]!r} "
            "doesn't match the code's own prefix"
        )
