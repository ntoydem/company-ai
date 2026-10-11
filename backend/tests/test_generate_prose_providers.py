"""Adım 5: PROSE_PROVIDER=anthropic — SDK'lar mock'lanır, gerçek ağ/anahtar hiç kullanılmaz.

Gemini yolunun bayt-aynı kaldığını (refactor güvenliği), bütçe/altyapı-hata ayrımını ve
anahtarın hiçbir çıktıda görünmediğini doğrular.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx
import pytest
import yaml

from seed_data.generator import generate_prose

FAKE_KEY = "sk-ant-totally-fake-secret-abc123xyz"  # pragma: allowlist secret — never a real key


def _rate_limit_error(status_code: int = 429) -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code=status_code, request=request)
    return anthropic.APIStatusError("rate limited", response=response, body=None)


class _FakeMessages:
    def __init__(self, fail_times: int = 0, status_code: int = 429) -> None:
        self.calls = 0
        self.fail_times = fail_times
        self.status_code = status_code

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise _rate_limit_error(self.status_code)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text='{"sections": []}')],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )


class _FakeClient:
    def __init__(self, fail_times: int = 0, status_code: int = 429) -> None:
        self.messages = _FakeMessages(fail_times, status_code)


def test_default_provider_is_gemini_and_resolves_default_model(monkeypatch, tmp_path) -> None:
    """Refactor-güvenlik: PROSE_PROVIDER yoksa client/model/tracker seçimi Adım-5-öncesiyle
    birebir aynı (gemini, DEFAULT_MODEL, tracker=None)."""
    monkeypatch.delenv("PROSE_PROVIDER", raising=False)
    monkeypatch.delenv("PROSE_MODEL", raising=False)
    monkeypatch.setattr(generate_prose, "PROSE_DIR", tmp_path)
    recorded: dict[str, object] = {}

    def fake_client(provider):
        recorded["client_provider"] = provider
        return object()

    monkeypatch.setattr(generate_prose, "_client", fake_client)

    def fake_generate_one(client, model, doc_id, raws, provider, tracker):
        recorded["model"] = model
        recorded["provider"] = provider
        recorded["tracker"] = tracker
        return []

    monkeypatch.setattr(generate_prose, "generate_one", fake_generate_one)

    rc = generate_prose.main(["--only", "FAKE-DOC-1"])

    assert rc == 0
    assert recorded["client_provider"] == "gemini"
    assert recorded["provider"] == "gemini"
    assert recorded["model"] == generate_prose.DEFAULT_MODEL
    assert recorded["tracker"] is None


def test_anthropic_missing_key_raises_systemexit_without_leaking_value(monkeypatch) -> None:
    monkeypatch.delenv("PROSE_ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        generate_prose._anthropic_client()
    assert FAKE_KEY not in str(exc_info.value)
    assert "PROSE_ANTHROPIC_API_KEY" in str(exc_info.value)


def test_api_key_never_appears_in_any_captured_output(monkeypatch, capsys) -> None:
    monkeypatch.setenv("PROSE_ANTHROPIC_API_KEY", FAKE_KEY)
    client = generate_prose._anthropic_client()
    assert FAKE_KEY not in repr(client)
    assert FAKE_KEY not in str(client)
    captured = capsys.readouterr()
    assert FAKE_KEY not in captured.out
    assert FAKE_KEY not in captured.err


def test_cost_tracker_known_model_pricing() -> None:
    tracker = generate_prose.CostTracker(
        provider="anthropic", model="claude-sonnet-5-5", budget_usd=15, max_tokens_per_run=200_000
    )
    tracker.record_usage(1_000_000, 500_000)
    # Sonnet 5.5: $2/MTok input, $10/MTok output (https://claude.com/pricing, 11.10.2026).
    assert tracker.estimated_cost_usd() == pytest.approx(2.0 + 5.0)
    assert tracker.call_count == 1


def test_cost_tracker_unknown_model_falls_back_to_token_guard() -> None:
    tracker = generate_prose.CostTracker(
        provider="anthropic", model="some-future-model", budget_usd=15, max_tokens_per_run=100
    )
    tracker.record_usage(60, 50)
    assert tracker.estimated_cost_usd() is None
    assert tracker.budget_exceeded() is True  # 110 >= 100 token guard, price unverifiable

    under_budget = generate_prose.CostTracker(
        provider="anthropic", model="some-future-model", budget_usd=15, max_tokens_per_run=100
    )
    under_budget.record_usage(10, 10)
    assert under_budget.budget_exceeded() is False


def test_budget_exceeded_stops_before_next_document_no_extra_call(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(generate_prose, "PROSE_DIR", tmp_path)
    monkeypatch.setenv("PROSE_ANTHROPIC_API_KEY", FAKE_KEY)
    monkeypatch.setenv("PROSE_BUDGET_USD", "5")
    calls = {"n": 0}

    def fake_call(client, model, system, user):
        calls["n"] += 1
        return {"sections": []}, (1_000_000, 500_000)  # ~$7 at sonnet-5-5 pricing, exceeds $5

    def fake_client(provider):
        return generate_prose._anthropic_client()

    monkeypatch.setattr(generate_prose, "_call_anthropic_with_backoff", fake_call)
    monkeypatch.setattr(generate_prose, "_client", fake_client)
    monkeypatch.setattr(generate_prose, "check_prose_document", lambda doc_id, prose, known: [])

    rc = generate_prose.main(
        ["--provider", "anthropic", "--only", "DOC-IZM-FIN-004", "--only", "DOC-YSV-FIN-009"]
    )

    assert calls["n"] == 1  # second document never called — budget checked before the call
    assert rc == 1


def test_anthropic_429_exponential_backoff_then_success(monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(generate_prose.time, "sleep", sleeps.append)
    client = _FakeClient(fail_times=2)

    payload, usage = generate_prose._call_anthropic_with_backoff(
        client, "claude-sonnet-5-5", "sys", "usr"
    )

    assert payload == {"sections": []}
    assert usage == (10, 5)
    assert client.messages.calls == 3
    assert sleeps == [2.0, 4.0]


def test_anthropic_529_exhausted_backoff_raises_infra_error(monkeypatch) -> None:
    monkeypatch.setattr(generate_prose.time, "sleep", lambda s: None)
    client = _FakeClient(fail_times=99, status_code=529)

    with pytest.raises(generate_prose._AnthropicInfraError):
        generate_prose._call_anthropic_with_backoff(client, "claude-sonnet-5-5", "sys", "usr")

    assert client.messages.calls == generate_prose.ANTHROPIC_BACKOFF_ATTEMPTS


def test_generate_one_anthropic_reports_infra_error_distinctly_from_content(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(generate_prose, "PROSE_DIR", tmp_path)

    def always_infra(client, model, system, user):
        raise generate_prose._AnthropicInfraError("429, 3 deneme sonunda hâlâ başarısız")

    monkeypatch.setattr(generate_prose, "_call_anthropic_with_backoff", always_infra)
    checked = {"called": False}
    monkeypatch.setattr(
        generate_prose,
        "check_prose_document",
        lambda *a, **k: checked.update(called=True) or [],
    )
    tracker = generate_prose.CostTracker(
        provider="anthropic", model="claude-sonnet-5-5", budget_usd=15, max_tokens_per_run=200_000
    )

    errors = generate_prose._generate_one_anthropic(
        object(), "claude-sonnet-5-5", "DOC-X", "sys", "usr", set(), tracker
    )

    assert errors and "altyapı hatası" in errors[0]
    assert not checked["called"]  # içerik doğrulaması hiç çağrılmadı — bu bir içerik reddi değil
    assert tracker.infra_error_count == 1
    assert tracker.content_reject_count == 0


def test_generate_one_anthropic_success_writes_real_model_and_tag(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(generate_prose, "PROSE_DIR", tmp_path)

    def fake_call(client, model, system, user):
        return {"sections": [{"heading": "H", "paragraphs": ["ok."]}]}, (10, 5)

    monkeypatch.setattr(generate_prose, "_call_anthropic_with_backoff", fake_call)
    monkeypatch.setattr(generate_prose, "check_prose_document", lambda *a, **k: [])
    tracker = generate_prose.CostTracker(
        provider="anthropic", model="claude-sonnet-5-5", budget_usd=15, max_tokens_per_run=200_000
    )

    errors = generate_prose._generate_one_anthropic(
        object(), "claude-sonnet-5-5", "DOC-X", "sys", "usr", set(), tracker
    )

    assert errors == []
    written = yaml.safe_load((Path(tmp_path) / "DOC-X.yaml").read_text(encoding="utf-8"))
    assert written["model"] == "claude-sonnet-5-5"
    assert written["tag"] == "AI_ASSUMPTION"
    assert tracker.call_count == 1
    assert tracker.input_tokens == 10
    assert tracker.output_tokens == 5
