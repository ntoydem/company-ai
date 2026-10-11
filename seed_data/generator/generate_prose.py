"""LLM prose batch, run once (SORU 1, docs/plans/PHASE_3_1_PLAN.md).

    python -m seed_data.generator.generate_prose [--only DOC-ID] [--force]
    python -m seed_data.generator.generate_prose --only DOC-ID --provider anthropic --force

Writes `prose/<DOC-ID>.yaml`, `tag: AI_ASSUMPTION`, committed to git. `make seed` never
calls this — the prod clone renders from the committed prose, no LLM/network needed
(docs/plans/PHASE_3_1_PLAN.md SORU 1). Not imported by `app/` (ADR-013); talks to the
OpenAI-compatible endpoint directly via `LLM_BASE_URL`/`LLM_API_KEY`/`PROSE_MODEL`.

Adım 5 (11.10.2026): optional second provider (`PROSE_PROVIDER=anthropic`, official `anthropic`
SDK) for retrying a document Gemini got stuck on (429/503 storms, not content rejections). The
default (`gemini`) path is untouched byte-for-byte — this is a NEW, separate code path, never a
rewrite of the existing one. Independent of `app/`'s own (deferred) `LLM_PROVIDER=anthropic`
(`app/services/llm/factory.py`) — this key is `PROSE_ANTHROPIC_API_KEY`, never confuse the two.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
import yaml
from openai import APIStatusError, OpenAI

from seed_data.generator import facts as facts_mod
from seed_data.generator.document_specs import SPECS, DocumentSpec
from seed_data.generator.validate_documents import check_prose_document

PROSE_DIR = Path(__file__).resolve().parent / "prose"
DEFAULT_MODEL = "gemini-3.5-flash"
CALL_SPACING_S = 13
RATE_LIMIT_WAIT_S = 65
MAX_ATTEMPTS = 3

# --- Adım 5: Anthropic sağlayıcısı (opsiyonel, PROSE_PROVIDER=anthropic) -------------------
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"
ANTHROPIC_CALL_SPACING_S = float(os.environ.get("PROSE_ANTHROPIC_CALL_SPACING_S", "3"))
ANTHROPIC_RETRYABLE_STATUS = (429, 529)
ANTHROPIC_BACKOFF_ATTEMPTS = 3
ANTHROPIC_BACKOFF_BASE_S = 2.0
ANTHROPIC_MAX_TOKENS = 4096

# Resmi fiyat kaynağı: https://claude.com/pricing (anthropic.com/pricing buraya 301 yönlendirir),
# WebFetch ile 11.10.2026'da doğrulandı. Fiyat tablosunda olmayan bir model için fiyat TAHMİN
# EDİLMEZ — CostTracker guard'ı o durumda token sayısına döner (PROSE_MAX_TOKENS_PER_RUN).
ANTHROPIC_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (2.0, 10.0),
}


@dataclass
class CostTracker:
    """Adım 5: Anthropic çağrılarının token/maliyet bütçesi. Gemini yolu bunu hiç kullanmaz."""

    provider: str
    model: str
    budget_usd: float
    max_tokens_per_run: int
    call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    infra_error_count: int = 0
    content_reject_count: int = 0

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.call_count += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def _pricing(self) -> tuple[float, float] | None:
        return ANTHROPIC_PRICING_USD_PER_MTOK.get(self.model)

    def estimated_cost_usd(self) -> float | None:
        price = self._pricing()
        if price is None:
            return None
        in_price, out_price = price
        in_cost = (self.input_tokens / 1_000_000) * in_price
        out_cost = (self.output_tokens / 1_000_000) * out_price
        return in_cost + out_cost

    def budget_exceeded(self) -> bool:
        cost = self.estimated_cost_usd()
        if cost is not None:
            return cost >= self.budget_usd
        return (self.input_tokens + self.output_tokens) >= self.max_tokens_per_run

    def summary_line(self) -> str:
        cost = self.estimated_cost_usd()
        cost_str = f"${cost:.4f}" if cost is not None else "fiyat doğrulanamadı"
        return (
            f"anthropic özet: {self.call_count} çağrı, {self.input_tokens}+{self.output_tokens} "
            f"token, tahmini maliyet {cost_str}, altyapı hatası {self.infra_error_count}, "
            f"içerik reddi {self.content_reject_count}"
        )


_SYSTEM_TR = """Sen kurgusal bir DEMO şirket belgesi için düz yazı metni yazan bir yardımcısın. \
Çıktın yalnızca aşağıdaki JSON şemasına uyan geçerli JSON olmalı, başka hiçbir şey yazma.
KURAL (çok önemli): Hiçbir rakam, tarih, para tutarı, oran, yüzde veya şirket/kişi adı YAZMA. \
Böyle bir bilgiye ihtiyaç duyduğunda YALNIZCA sana verilen [[token]] placeholder'larından \
birini kullan (örn. "kapasite [[capacity_mw]] olarak belirlenmiştir"). Listede olmayan bir \
placeholder uydurma. Madde/bölüm numaraları başlıklarda zaten var, metin içinde tekrar \
numara icat etme.
KURAL 2 (düzeltme, 11.10.2026): Sözleşme boilerplate'ini GENEL tut — token ile \
verilmeyen somut bir hüküm icat etme (örn. belirli bir cezasız erken ödeme kuralı, \
belirli bir cure/düzeltme süresi, belirli bir yetkili mahkeme/hukuk sistemi, belirli \
bir faiz hesap yöntemi). Her somut ifade yalnız sana token'larla verilen olgulara \
dayanmalı; olmayan bir detayı tahmin etmek yerine genel/muğlak bir ifade kullan.
Bu resmi/teknik bir demo belgesidir, gerçek değildir; ton resmi ve kurumsal olmalı."""

_SYSTEM_EN = """You write prose for a FICTIONAL demo company document. Your output must be \
valid JSON matching the schema below and nothing else.
RULE (critical): Never write any digit, date, currency amount, ratio, percentage or \
company/person name. Whenever such a value is needed, use ONLY one of the [[token]] \
placeholders given to you (e.g. "the tenor of the Facility is [[tenor_years]]"). Never \
invent a placeholder that is not in the list. Section numbers are already in the headings;
do not invent additional numbering inside the prose.
RULE 2 (correction, 11.10.2026): Keep contractual boilerplate GENERIC — never invent a \
specific substantive provision that is not backed by a given token (e.g. a specific \
early-repayment-without-penalty rule, a specific cure period, a specific governing \
court/legal system, a specific interest calculation method). Every substantive \
statement must rest only on the facts given to you via tokens; use a general/vague \
phrasing instead of guessing a missing detail.
This is a formal/technical demo document, not a real one; keep the tone formal and corporate."""

_SCHEMA_NOTE = """JSON şeması:
{"sections": [{"heading": "<başlık>", "paragraphs": ["<2-4 kısa paragraf>", ...]}]}
Bölüm sayısı ve başlıkları AŞAĞIDA verilenlerle birebir aynı ve aynı sırada olmalı. \
Her paragraf 2-4 cümle, kısa ve öz olsun (bir sayfaya sığmalı)."""


def _gemini_client() -> OpenAI:
    base_url = os.environ.get(
        "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise SystemExit("LLM_API_KEY not set")
    return OpenAI(base_url=base_url, api_key=api_key, timeout=60)


def _anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("PROSE_ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("PROSE_ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key, timeout=60)


def _client(provider: str) -> OpenAI | anthropic.Anthropic:
    return _anthropic_client() if provider == "anthropic" else _gemini_client()


def _build_prompt(
    doc_id: str,
    spec: DocumentSpec,
    facts: dict[str, str],
    language: str,
    suppressed_placeholders: frozenset[str] = frozenset(),
) -> tuple[str, str]:
    """Düzeltme (11.10.2026): `suppressed_placeholders` — bir facts anahtarı (`language`
    dışında) teknik olarak orada ama "tanımsız" bir not metnine çözülüyorsa (örn. taslak
    bir belgenin `effective_date`'i "henüz belirlenmedi" döner) LLM'e hiç ÖNERİLMEZ;
    `known_placeholders` (check_prose_document) hâlâ kabul eder, yalnız teşvik edilmez."""
    headings = spec.section_headings_tr if language == "tr" else spec.section_headings_en
    placeholders = sorted(k for k in facts if k != "language" and k not in suppressed_placeholders)
    system = _SYSTEM_TR if language == "tr" else _SYSTEM_EN
    user = (
        f"Belge: {facts['title']} ({doc_id})\n"
        f"Kullanılabilir placeholder'lar: {', '.join(f'[[{p}]]' for p in placeholders)}\n"
        f"Bölüm başlıkları (aynı sırayla, aynen): {json.dumps(headings, ensure_ascii=False)}\n\n"
        f"{_SCHEMA_NOTE}"
    )
    return system, user


def _call_llm(client: OpenAI, model: str, system: str, user: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("empty LLM response")
    return dict(json.loads(content))


def _write_prose(doc_id: str, model: str, sections: list[Any]) -> None:
    prose = {"doc_id": doc_id, "model": model, "tag": "AI_ASSUMPTION", "sections": sections}
    (PROSE_DIR / f"{doc_id}.yaml").write_text(
        yaml.safe_dump(prose, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def _write_rejected(doc_id: str, errors: list[str]) -> None:
    rejected_path = PROSE_DIR / f"{doc_id}.rejected.yaml"
    rejected_path.write_text(
        yaml.safe_dump({"doc_id": doc_id, "errors": errors}, allow_unicode=True),
        encoding="utf-8",
    )


def _generate_one_gemini(
    client: OpenAI, model: str, doc_id: str, system: str, user: str, known: set[str]
) -> list[str]:
    """Gemini path — byte-identical to the pre-Adım-5 `generate_one` body."""
    last_errors: list[str] = ["no attempt made"]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            sections = _call_llm(client, model, system, user).get("sections", [])
        except APIStatusError as exc:
            if exc.status_code in (429, 503):
                print(f"  {doc_id}: {exc.status_code}, {RATE_LIMIT_WAIT_S}s bekleniyor...")
                time.sleep(RATE_LIMIT_WAIT_S)
                continue
            raise
        except (json.JSONDecodeError, ValueError) as exc:
            last_errors = [f"{doc_id}: LLM çıktısı JSON değil: {exc}"]
            continue

        prose = {"doc_id": doc_id, "model": model, "tag": "AI_ASSUMPTION", "sections": sections}
        errors = check_prose_document(doc_id, prose, known)
        if not errors:
            _write_prose(doc_id, model, sections)
            return []
        last_errors = errors
        print(f"  {doc_id}: deneme {attempt}/{MAX_ATTEMPTS} reddedildi ({len(errors)} sorun)")

    _write_rejected(doc_id, last_errors)
    return last_errors


class _AnthropicInfraError(Exception):
    """429/529 survived ANTHROPIC_BACKOFF_ATTEMPTS backoff retries — infra, not content."""


def _strip_markdown_json_fence(text: str) -> str:
    """Claude sık sık geçerli JSON'u ```json ... ``` içine sarar (sistem promptu yalnız JSON
    istese de) — OpenAI'nin `response_format=json_object`'inin Anthropic'te karşılığı yok."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped


def _call_anthropic_with_backoff(
    client: anthropic.Anthropic, model: str, system: str, user: str
) -> tuple[str, tuple[int, int]]:
    """One content-attempt's worth of 429/529 exponential backoff, SEPARATE from the outer
    MAX_ATTEMPTS content-validation budget (Naci'nin "içerik ihlali ile altyapı hatasını ayır"
    talimatı — Gemini'nin 429'u content-retry bütçesini tükettiği PF-1 düzeltme olayından).
    Returns the RAW text + usage — JSON parsing is the caller's job, so a real (billed) call's
    usage is recorded by the caller even when the output turns out not to be valid JSON."""
    backoff_s = ANTHROPIC_BACKOFF_BASE_S
    for infra_attempt in range(1, ANTHROPIC_BACKOFF_ATTEMPTS + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=ANTHROPIC_MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIStatusError as exc:
            retryable = exc.status_code in ANTHROPIC_RETRYABLE_STATUS
            if retryable and infra_attempt < ANTHROPIC_BACKOFF_ATTEMPTS:
                print(
                    f"  anthropic {exc.status_code}, {backoff_s:.0f}s bekleniyor "
                    f"(deneme {infra_attempt}/{ANTHROPIC_BACKOFF_ATTEMPTS})..."
                )
                time.sleep(backoff_s)
                backoff_s *= 2
                continue
            if retryable:
                message = (
                    f"{exc.status_code}, {ANTHROPIC_BACKOFF_ATTEMPTS} deneme sonunda hâlâ başarısız"
                )
                raise _AnthropicInfraError(message) from exc
            raise
        else:
            text = "".join(block.text for block in response.content if block.type == "text")
            usage = (response.usage.input_tokens, response.usage.output_tokens)
            return text, usage
    raise AssertionError("unreachable")  # loop always returns or raises


def _generate_one_anthropic(
    client: anthropic.Anthropic,
    model: str,
    doc_id: str,
    system: str,
    user: str,
    known: set[str],
    tracker: CostTracker,
) -> list[str]:
    last_errors: list[str] = ["no attempt made"]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if tracker.budget_exceeded():
            last_errors = [f"{doc_id}: bütçe aşıldı ({tracker.summary_line()}), üretim durduruldu"]
            break
        try:
            text, usage = _call_anthropic_with_backoff(client, model, system, user)
        except _AnthropicInfraError as exc:
            tracker.infra_error_count += 1
            last_errors = [f"{doc_id}: altyapı hatası — {exc}"]
            print(f"  {doc_id}: altyapı hatası, içerik reddi DEĞİL — {exc}")
            break

        # Çağrı gerçekleşti (ücretlendirildi) — JSON parse edilemese bile usage kaydedilir,
        # yoksa bütçe guard'ı başarısız denemelerin gerçek maliyetini kaçırır.
        tracker.record_usage(*usage)
        try:
            payload = dict(json.loads(_strip_markdown_json_fence(text)))
        except (json.JSONDecodeError, ValueError) as exc:
            tracker.content_reject_count += 1
            snippet = text[:200].replace("\n", " ")
            last_errors = [f"{doc_id}: LLM çıktısı JSON değil: {exc} — ham çıktı: {snippet!r}"]
            print(f"  {doc_id}: LLM çıktısı JSON değil, ham çıktı önizleme: {snippet!r}")
            continue

        sections = payload.get("sections", [])
        prose = {"doc_id": doc_id, "model": model, "tag": "AI_ASSUMPTION", "sections": sections}
        errors = check_prose_document(doc_id, prose, known)
        if not errors:
            _write_prose(doc_id, model, sections)
            return []
        tracker.content_reject_count += 1
        last_errors = [f"{doc_id}: içerik reddi — {e}" for e in errors]
        print(
            f"  {doc_id}: deneme {attempt}/{MAX_ATTEMPTS} reddedildi (içerik, {len(errors)} sorun)"
        )

    _write_rejected(doc_id, last_errors)
    return last_errors


def generate_one(
    client: OpenAI | anthropic.Anthropic,
    model: str,
    doc_id: str,
    raws: dict[str, Any],
    provider: str = "gemini",
    tracker: CostTracker | None = None,
) -> list[str]:
    """Returns validation errors (empty = success, written to disk)."""
    spec = SPECS[doc_id]
    by_id = {doc["id"]: doc for raw in raws.values() for doc in raw.get("documents", [])}
    doc = by_id[doc_id]
    language = doc["language"]
    facts = facts_mod.build_facts(doc, raws)
    known = set(facts) - {"language"}
    # Düzeltme (11.10.2026): taslak (effective_date yok) belgelerde "effective_date"
    # placeholder'ı LLM'e önerilmez — değeri gerçek bir olgu değil, "henüz belirlenmedi"
    # notu (DOC-YSV-FIN-010 bulgusu).
    suppressed = {"effective_date"} if doc.get("effective_date") is None else frozenset()
    system, user = _build_prompt(doc_id, spec, facts, language, suppressed)

    if provider == "anthropic":
        assert isinstance(client, anthropic.Anthropic)
        assert tracker is not None
        return _generate_one_anthropic(client, model, doc_id, system, user, known, tracker)
    assert isinstance(client, OpenAI)
    return _generate_one_gemini(client, model, doc_id, system, user, known)


HAND_EDITED_KEY = "hand_edited"


def is_hand_edited(prose_path: Path) -> bool:
    """A prose file carrying a top-level `hand_edited:` note was corrected by hand after
    generation (Phase 3.2c: seven sentences that close real content gaps). Regenerating
    it — even with `--force` — would silently undo those corrections, so it is never
    overwritten; delete the key deliberately if you really want a fresh LLM draft."""
    if not prose_path.exists():
        return False
    data = yaml.safe_load(prose_path.read_text(encoding="utf-8"))
    return isinstance(data, dict) and bool(data.get(HAND_EDITED_KEY))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate_prose")
    parser.add_argument("--only", action="append", default=None, help="tek belge, tekrarlanabilir")
    parser.add_argument("--force", action="store_true", help="var olan prose'u da yeniden üret")
    parser.add_argument(
        "--provider",
        choices=("gemini", "anthropic"),
        default=os.environ.get("PROSE_PROVIDER", "gemini"),
        help="varsayılan gemini — davranış bayt-aynı kalır (Adım 5)",
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)
    if args.model is None:
        args.model = (
            os.environ.get("PROSE_ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            if args.provider == "anthropic"
            else os.environ.get("PROSE_MODEL", DEFAULT_MODEL)
        )

    PROSE_DIR.mkdir(parents=True, exist_ok=True)
    raws = facts_mod.load_raws()
    client = _client(args.provider)
    tracker = (
        CostTracker(
            provider=args.provider,
            model=args.model,
            budget_usd=float(os.environ.get("PROSE_BUDGET_USD", "15")),
            max_tokens_per_run=int(os.environ.get("PROSE_MAX_TOKENS_PER_RUN", "200000")),
        )
        if args.provider == "anthropic"
        else None
    )
    call_spacing = ANTHROPIC_CALL_SPACING_S if args.provider == "anthropic" else CALL_SPACING_S

    doc_ids = args.only or list(SPECS)
    failures: dict[str, list[str]] = {}
    for i, doc_id in enumerate(doc_ids):
        prose_path = PROSE_DIR / f"{doc_id}.yaml"
        if is_hand_edited(prose_path):
            print(f"atlandı (elle düzenlenmiş, `{HAND_EDITED_KEY}:`; --force ezmez): {doc_id}")
            continue
        if prose_path.exists() and not args.force:
            print(f"atlandı (zaten var): {doc_id}")
            continue
        if tracker is not None and tracker.budget_exceeded():
            print(f"bütçe aşıldı, {doc_id} ve sonrası üretilmiyor ({tracker.summary_line()})")
            failures[doc_id] = ["bütçe aşıldı, çağrı yapılmadı"]
            break
        if i > 0:
            time.sleep(call_spacing)
        print(f"üretiliyor: {doc_id}")
        errors = generate_one(client, args.model, doc_id, raws, args.provider, tracker)
        if errors:
            failures[doc_id] = errors

    if tracker is not None:
        print(tracker.summary_line())

    if failures:
        print(f"\n{len(failures)} belge reddedildi:")
        for doc_id, errors in failures.items():
            print(f"  {doc_id}:")
            for error in errors[:5]:
                print(f"    - {error}")
        return 1
    print(f"\ntamamlandı: {len(doc_ids) - len(failures)} belge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
