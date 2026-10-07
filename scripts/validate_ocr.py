"""Quality gate (c) for scanned demo documents (Naci, 07.10.2026): compare what the OCR
worker actually stored in `document_pages` with the facts the generator printed
(`manifest.json` → `key_facts_used`), so a tesseract misread like "%20" → "9020"
(DOC-CO-ADM-003, 06.10.2026) is caught after ingestion, not by an eval run weeks later.

    make validate-ocr                 # scanned_pdf documents only (the OCR path)
    make validate-ocr ARGS="--all"    # digital ones too (text layer kept by --skip-text)

Needs the live database (reads `documents`/`document_pages`), so it is a separate target —
deliberately NOT part of `make lint`. `validate_documents.py` checks the *digital* PDF text
before upload; this script checks the *ingested* text afterwards — the only place the two
can legitimately differ is OCR, which is exactly what is measured here.

Comparison is format-insensitive: values and page text are reduced to canonical number /
date tokens with `scripts.eval_lib.fact_tokens` (`%20` = `yüzde 20` = `20`,
`15 Kasım 2021` = `15.11.2021`, `45.000.000 EUR` = `45,000,000 EUR`); text facts
(`repayment_profile`, `ced_status`, …) are compared as case- and whitespace-folded
substrings. Each fact is looked for on the page(s) whose prose section carries its
`[[token]]` (`page_map`), falling back to the whole document when the token is not in a
section (cover-page facts). Exit code 1 on any mismatch; no LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select

from app.core.db import get_session_factory
from app.models.document import Document
from app.models.document_page import DocumentPage
from scripts.eval_lib import fact_tokens

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "seed_data" / "documents" / "manifest.json"
DEFAULT_PROSE_DIR = REPO_ROOT / "seed_data" / "generator" / "prose"
_TOKEN_RE = re.compile(r"\[\[(\w+)\]\]")


@dataclass(frozen=True)
class FactResult:
    external_ref: str
    field: str
    value: str
    pages: tuple[int, ...]
    ok: bool
    detail: str  # what the OCR text holds instead (numbers/dates on those pages), on mismatch


def _fold(text: str) -> str:
    # Turkish dotted capital İ casefolds to "i̇" (two code points) — map it first.
    return " ".join(text.replace("İ", "i").split()).casefold()


def expected_pages(prose: dict[str, Any], page_map: dict[str, int], field: str) -> tuple[int, ...]:
    """Pages whose prose section mentions `[[field]]`; empty when the token is not used in
    any section (cover/meta facts) — the caller then searches every page."""
    pages: list[int] = []
    for section in prose.get("sections", []):
        body = section.get("heading", "") + " " + " ".join(section.get("paragraphs", []))
        if field in _TOKEN_RE.findall(body):
            page = page_map.get(section["heading"])
            if page is not None and page not in pages:
                pages.append(page)
    return tuple(pages)


def compare_fact(value: str, text: str) -> tuple[bool, str]:
    """True when every number/date token of `value` is in `text` (format-insensitive), or
    — for a value without numbers — when the folded value is a substring of the folded
    text. The detail names the numeric/date tokens the text does carry, for the report."""
    wanted = fact_tokens(value)
    have = fact_tokens(text)
    if wanted:
        ok = wanted <= have
        return ok, "" if ok else "OCR metnindeki sayı/tarih tokenları: " + ", ".join(sorted(have))
    ok = _fold(value) in _fold(text)
    return ok, "" if ok else "metin olarak bulunamadı"


def check_entry(
    entry: dict[str, Any], pages: dict[int, str], prose: dict[str, Any]
) -> list[FactResult]:
    results = []
    for field, value in entry.get("key_facts_used", {}).items():
        where = expected_pages(prose, entry.get("page_map", {}), field)
        candidates = [p for p in where if p in pages] or sorted(pages)
        text = "\n".join(pages[p] for p in candidates)
        ok, detail = compare_fact(str(value), text)
        results.append(
            FactResult(entry["external_ref"], field, str(value), tuple(candidates), ok, detail)
        )
    return results


def _load_pages(session: Any, external_ref: str) -> dict[int, str] | None:
    document = session.scalars(
        select(Document).where(Document.external_ref == external_ref)
    ).first()
    if document is None:
        return None
    rows = session.execute(
        select(DocumentPage.page_number, DocumentPage.text).where(
            DocumentPage.document_id == document.id
        )
    ).all()
    return {int(n): t or "" for n, t in rows}


def run(manifest_path: Path, prose_dir: Path, *, include_digital: bool) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [
        e for e in manifest["documents"] if include_digital or e.get("source_type") == "scanned_pdf"
    ]
    results: list[FactResult] = []
    missing: list[str] = []
    with get_session_factory()() as session:
        for entry in entries:
            pages = _load_pages(session, entry["external_ref"])
            if not pages:
                missing.append(entry["external_ref"])
                continue
            prose_path = prose_dir / f"{entry['external_ref']}.yaml"
            prose = (
                yaml.safe_load(prose_path.read_text(encoding="utf-8"))
                if prose_path.exists()
                else {}
            )
            results.extend(check_entry(entry, pages, prose))

    bad = [r for r in results if not r.ok]
    scope = "tüm belgeler" if include_digital else "yalnızca scanned_pdf"
    print(
        f"validate-ocr — {scope}: {len(entries)} belge, {len(results)} anahtar olgu, "
        f"{len(results) - len(bad)} eşleşti, {len(bad)} FARK, DB'de olmayan: {len(missing)}"
    )
    print()
    print("| Belge | Sayfa | Alan | Beklenen (manifest) | Durum | Ayrıntı |")
    print("|---|---|---|---|---|---|")
    for r in results:
        page = ",".join(str(p) for p in r.pages)
        print(
            f"| {r.external_ref} | {page} | {r.field} | {r.value} | "
            f"{'✅' if r.ok else '❌ FARK'} | {r.detail} |"
        )
    for ref in missing:
        print(f"| {ref} | – | – | – | ⏭ DB'de yok / sayfa yok | |")
    return 1 if bad or missing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_ocr")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--prose-dir", type=Path, default=DEFAULT_PROSE_DIR)
    parser.add_argument("--all", action="store_true", help="digital_pdf documents too")
    args = parser.parse_args(argv)
    return run(args.manifest, args.prose_dir, include_digital=args.all)


if __name__ == "__main__":
    sys.exit(main())
