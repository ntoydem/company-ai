"""LLM prose batch, run once (SORU 1, docs/plans/PHASE_3_1_PLAN.md).

    python -m seed_data.generator.generate_prose [--only DOC-ID] [--force]

Writes `prose/<DOC-ID>.yaml`, `tag: AI_ASSUMPTION`, committed to git. `make seed` never
calls this — the prod clone renders from the committed prose, no LLM/network needed
(docs/plans/PHASE_3_1_PLAN.md SORU 1). Not imported by `app/` (ADR-013); talks to the
OpenAI-compatible endpoint directly via `LLM_BASE_URL`/`LLM_API_KEY`/`PROSE_MODEL`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

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

_SYSTEM_TR = """Sen kurgusal bir DEMO şirket belgesi için düz yazı metni yazan bir yardımcısın. \
Çıktın yalnızca aşağıdaki JSON şemasına uyan geçerli JSON olmalı, başka hiçbir şey yazma.
KURAL (çok önemli): Hiçbir rakam, tarih, para tutarı, oran, yüzde veya şirket/kişi adı YAZMA. \
Böyle bir bilgiye ihtiyaç duyduğunda YALNIZCA sana verilen [[token]] placeholder'larından \
birini kullan (örn. "kapasite [[capacity_mw]] olarak belirlenmiştir"). Listede olmayan bir \
placeholder uydurma. Madde/bölüm numaraları başlıklarda zaten var, metin içinde tekrar \
numara icat etme.
Bu resmi/teknik bir demo belgesidir, gerçek değildir; ton resmi ve kurumsal olmalı."""

_SYSTEM_EN = """You write prose for a FICTIONAL demo company document. Your output must be \
valid JSON matching the schema below and nothing else.
RULE (critical): Never write any digit, date, currency amount, ratio, percentage or \
company/person name. Whenever such a value is needed, use ONLY one of the [[token]] \
placeholders given to you (e.g. "the tenor of the Facility is [[tenor_years]]"). Never \
invent a placeholder that is not in the list. Section numbers are already in the headings;
do not invent additional numbering inside the prose.
This is a formal/technical demo document, not a real one; keep the tone formal and corporate."""

_SCHEMA_NOTE = """JSON şeması:
{"sections": [{"heading": "<başlık>", "paragraphs": ["<2-4 kısa paragraf>", ...]}]}
Bölüm sayısı ve başlıkları AŞAĞIDA verilenlerle birebir aynı ve aynı sırada olmalı. \
Her paragraf 2-4 cümle, kısa ve öz olsun (bir sayfaya sığmalı)."""


def _client() -> OpenAI:
    base_url = os.environ.get(
        "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise SystemExit("LLM_API_KEY not set")
    return OpenAI(base_url=base_url, api_key=api_key, timeout=60)


def _build_prompt(
    doc_id: str, spec: DocumentSpec, facts: dict[str, str], language: str
) -> tuple[str, str]:
    headings = spec.section_headings_tr if language == "tr" else spec.section_headings_en
    placeholders = sorted(k for k in facts if k != "language")
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


def generate_one(client: OpenAI, model: str, doc_id: str, raws: dict[str, Any]) -> list[str]:
    """Returns validation errors (empty = success, written to disk)."""
    spec = SPECS[doc_id]
    by_id = {doc["id"]: doc for raw in raws.values() for doc in raw.get("documents", [])}
    doc = by_id[doc_id]
    language = doc["language"]
    facts = facts_mod.build_facts(doc, raws)
    known = set(facts) - {"language"}
    system, user = _build_prompt(doc_id, spec, facts, language)

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
            (PROSE_DIR / f"{doc_id}.yaml").write_text(
                yaml.safe_dump(prose, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            return []
        last_errors = errors
        print(f"  {doc_id}: deneme {attempt}/{MAX_ATTEMPTS} reddedildi ({len(errors)} sorun)")

    rejected_path = PROSE_DIR / f"{doc_id}.rejected.yaml"
    rejected_path.write_text(
        yaml.safe_dump({"doc_id": doc_id, "errors": last_errors}, allow_unicode=True),
        encoding="utf-8",
    )
    return last_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate_prose")
    parser.add_argument("--only", action="append", default=None, help="tek belge, tekrarlanabilir")
    parser.add_argument("--force", action="store_true", help="var olan prose'u da yeniden üret")
    parser.add_argument("--model", default=os.environ.get("PROSE_MODEL", DEFAULT_MODEL))
    args = parser.parse_args(argv)

    PROSE_DIR.mkdir(parents=True, exist_ok=True)
    raws = facts_mod.load_raws()
    client = _client()

    doc_ids = args.only or list(SPECS)
    failures: dict[str, list[str]] = {}
    for i, doc_id in enumerate(doc_ids):
        prose_path = PROSE_DIR / f"{doc_id}.yaml"
        if prose_path.exists() and not args.force:
            print(f"atlandı (zaten var): {doc_id}")
            continue
        if i > 0:
            time.sleep(CALL_SPACING_S)
        print(f"üretiliyor: {doc_id}")
        errors = generate_one(client, args.model, doc_id, raws)
        if errors:
            failures[doc_id] = errors

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
