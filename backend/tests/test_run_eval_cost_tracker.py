"""`scripts.run_eval.CostTracker` — pure logic, no server/DB (İş Emri 2026-10-11-C Adım 3).
`eval_lib.py`'nin kendi test deseniyle aynı: ağ çağrısı olmadan saf hesaplama testi."""

from __future__ import annotations

import json

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


# ---------------------------------------------------------------- İş Emri 2026-10-15F0 A7


def test_spend_is_kept_per_model() -> None:
    tracker = CostTracker(budget_usd=None)
    tracker.add("claude-haiku-5-5", tokens_in=1_000_000, tokens_out=0)
    tracker.add("claude-haiku-5-5", tokens_in=0, tokens_out=1_000_000)
    tracker.add("claude-sonnet-5-5", tokens_in=1_000_000, tokens_out=0)
    assert tracker.spent_by_model == {"claude-haiku-5-5": 0.60, "claude-sonnet-5-5": 2.0}
    assert tracker.calls_by_model == {"claude-haiku-5-5": 2, "claude-sonnet-5-5": 1}
    assert tracker.tokens_by_model["claude-haiku-5-5"] == (1_000_000, 1_000_000)
    summary = tracker.summary()
    assert summary["spent_usd"] == 2.6
    assert summary["by_model"]["claude-sonnet-5-5"] == {
        "calls": 1,
        "tokens_in": 1_000_000,
        "tokens_out": 0,
        "usd": 2.0,
    }


def test_cost_from_llm_log_attributes_plan_calls_to_sonnet() -> None:
    """The backend logs one `llm call` line per model call with the request's id; the eval's
    own requests are summed per model, the background metadata loop (no matching id) and
    non-JSON noise are ignored."""
    from scripts.run_eval import cost_from_llm_log

    def line(message: str, request_id: str, model: str, tokens_in: int, tokens_out: int) -> str:
        return json.dumps(
            {
                "message": message,
                "request_id": request_id,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            }
        )

    lines = [
        "INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.",
        line("llm call", "r1", "claude-haiku-5-5", 1_000_000, 0),
        line("llm call", "r1", "claude-sonnet-5-5", 1_000_000, 100_000),
        line("llm call", "bg", "claude-haiku-5-5", 1_000_000, 0),
        line("http request", "r1", "claude-sonnet-5-5", 9, 9),
    ]
    tracker = cost_from_llm_log(lines, request_ids=["r1"])
    assert tracker.calls_by_model == {"claude-haiku-5-5": 1, "claude-sonnet-5-5": 1}
    assert tracker.spent_by_model["claude-haiku-5-5"] == 0.10
    assert tracker.spent_by_model["claude-sonnet-5-5"] == 3.0
    # without a request filter every `llm call` line counts
    assert cost_from_llm_log(lines).calls_by_model["claude-haiku-5-5"] == 2
