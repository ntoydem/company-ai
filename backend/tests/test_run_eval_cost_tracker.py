"""`scripts.run_eval.CostTracker` — pure logic, no server/DB (İş Emri 2026-10-11-C Adım 3).
`eval_lib.py`'nin kendi test deseniyle aynı: ağ çağrısı olmadan saf hesaplama testi."""

from __future__ import annotations

from scripts.run_eval import CostTracker


def test_known_models_accumulate_cost() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add("claude-haiku-5-5", tokens_in=1_000_000, tokens_out=1_000_000)
    assert tracker.spent_usd == 0.10 + 0.50
    tracker.add("claude-sonnet-5-5", tokens_in=1_000_000, tokens_out=1_000_000)
    assert tracker.spent_usd == 0.10 + 0.50 + 2.0 + 10.0
    assert tracker.unpriced_model_calls == 0


def test_gemini_is_free_tier_zero_cost() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add("gemini-3.5-flash-lite", tokens_in=5_000_000, tokens_out=5_000_000)
    assert tracker.spent_usd == 0.0


def test_unknown_model_is_counted_not_priced() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add("some-future-model", tokens_in=1_000_000, tokens_out=1_000_000)
    assert tracker.spent_usd == 0.0
    assert tracker.unpriced_model_calls == 1


def test_none_model_is_treated_as_unknown() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add(None, tokens_in=100, tokens_out=100)
    assert tracker.unpriced_model_calls == 1


def test_no_budget_never_exceeded() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add("claude-sonnet-5-5", tokens_in=10_000_000, tokens_out=10_000_000)
    assert not tracker.budget_exceeded()


def test_budget_exceeded_at_or_above_threshold() -> None:
    tracker = CostTracker(budget_usd=1.0)
    # 1 MTok input Sonnet 5.5 = $2.0, already over budget.
    tracker.add("claude-sonnet-5-5", tokens_in=1_000_000, tokens_out=0)
    assert tracker.budget_exceeded()


def test_budget_not_exceeded_below_threshold() -> None:
    tracker = CostTracker(budget_usd=1.0)
    tracker.add("claude-haiku-5-5", tokens_in=1_000_000, tokens_out=0)
    assert tracker.spent_usd == 0.10
    assert not tracker.budget_exceeded()
