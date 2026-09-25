"""Generated-content validator (docs/plans/PHASE_3_1_PLAN.md §5).

    python -m seed_data.generator.validate_documents [--prose-only] [--manifest FILE]

`--prose-only` checks `prose/*.yaml` (P1/P2): no digit run of 3+, no currency token, no
unwhitelisted company-like name, every placeholder is known, headings/count match
`document_specs.py`. Without the flag it also checks the rendered PDFs named in
`manifest.json` (G1-G6): banner, name whitelist, project isolation, and that every fact
value the document was built from actually appears in its text. Exit 0 only on 0 errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf
import yaml

from seed_data.generator import facts as facts_mod
from seed_data.generator.document_specs import SPECS
from seed_data.generator.generate_documents import _TOKEN_RE, DEFAULT_OUT, PROSE_DIR
from seed_data.generator.validate_ledger import _NAME_PATTERN

NUMBER_PATTERN = re.compile(r"\d{3,}")
CURRENCY_PATTERN = re.compile(r"\b(EUR|USD|TRY)\b|[€$₺]")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def scan_prose_text(text: str) -> list[str]:
    """P1: numbers/currency/names a real value could leak through as. Clause references
    like "Madde 12" or "Clause 5.2" never trigger this — they are 1-2 digit runs, and
    `\\d{3,}` only matches 3-or-more consecutive digits (verified by
    `test_validate_documents.py::test_clause_numbering_does_not_trigger_number_check`;
    a document would need 100+ numbered articles to collide, and none here does)."""
    stripped = _TOKEN_RE.sub("", text)
    issues = []
    for match in NUMBER_PATTERN.finditer(stripped):
        issues.append(f"3+ haneli sayı: {match.group()!r}")
    for match in CURRENCY_PATTERN.finditer(stripped):
        issues.append(f"para birimi ibaresi: {match.group()!r}")
    for match in _NAME_PATTERN.finditer(stripped):
        issues.append(f"şirket adı kalıbı: {match.group()!r}")
    return issues


def check_prose_document(
    doc_id: str, prose: dict[str, Any], known_placeholders: set[str]
) -> list[str]:
    """P1 + P2 for one `prose/<DOC-ID>.yaml`."""
    errors: list[str] = []
    spec = SPECS.get(doc_id)
    if spec is None:
        return [f"{doc_id}: document_specs.py'de tanımlı değil"]
    expected_headings = spec.section_headings_tr or spec.section_headings_en
    sections = prose.get("sections", [])
    if len(sections) != len(expected_headings):
        errors.append(
            f"{doc_id}: {len(sections)} bölüm üretildi, {len(expected_headings)} bekleniyordu"
        )
    for i, expected_heading in enumerate(expected_headings):
        if i >= len(sections):
            break
        section = sections[i]
        if section.get("heading") != expected_heading:
            errors.append(
                f"{doc_id}: section[{i}].heading {section.get('heading')!r} != {expected_heading!r}"
            )
        for issue in scan_prose_text(section.get("heading", "")):
            errors.append(f"{doc_id}: section[{i}].heading: {issue}")
        paragraphs = section.get("paragraphs", [])
        if not paragraphs:
            errors.append(f"{doc_id}: section[{i}] paragrafsız")
        for j, paragraph in enumerate(paragraphs):
            for issue in scan_prose_text(paragraph):
                errors.append(f"{doc_id}: section[{i}].paragraphs[{j}]: {issue}")
            for token in _TOKEN_RE.findall(paragraph):
                if token not in known_placeholders:
                    errors.append(f"{doc_id}: section[{i}].paragraphs[{j}]: bilinmeyen [[{token}]]")
    return errors


def validate_prose(prose_dir: Path = PROSE_DIR) -> Report:
    report = Report()
    raws = facts_mod.load_raws()
    by_id = {doc["id"]: doc for raw in raws.values() for doc in raw.get("documents", [])}
    for doc_id in SPECS:
        path = prose_dir / f"{doc_id}.yaml"
        if not path.exists():
            report.error(f"{doc_id}: prose/{doc_id}.yaml yok — `make prose` çalıştırılmalı")
            continue
        prose = yaml.safe_load(path.read_text(encoding="utf-8"))
        if prose.get("tag") != "AI_ASSUMPTION":
            report.error(f"{doc_id}: prose tag'i AI_ASSUMPTION olmalı")
        doc = by_id[doc_id]
        facts = facts_mod.build_facts(doc, raws)
        known = set(facts) - {"language"}
        for error in check_prose_document(doc_id, prose, known):
            report.error(error)
    return report


# --- G1-G6: generated PDFs, via manifest.json ---


def _extract_text(path: Path) -> str:
    with pymupdf.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def validate_generated(manifest_path: Path) -> Report:
    report = Report()
    if not manifest_path.exists():
        report.error(f"{manifest_path} yok — `make seed` (veya generate_documents) çalıştırılmalı")
        return report
    manifest = _load_manifest(manifest_path)
    raws = facts_mod.load_raws()
    banners = raws["company"]["demo_banners"]

    entries = manifest["documents"]
    # G6: manifest.json must render exactly document_specs.SPECS, no more, no fewer — the
    # overall count/distribution sanity check lives in validate_ledger.py's
    # check_document_distribution (Phase 5.1: the target is no longer a single fixed 15).
    expected_ids = {doc_id for doc_id, spec in SPECS.items()}
    manifest_ids = {e["external_ref"] for e in entries}
    if manifest_ids != expected_ids:
        report.error(
            f"manifest.json ↔ document_specs.py uyuşmuyor: {manifest_ids ^ expected_ids} (G6)"
        )

    for entry in entries:
        doc_id = entry["external_ref"]
        digital_name = entry["digital_file"] or entry["file"]
        digital_path = manifest_path.parent / digital_name
        if not digital_path.exists():
            report.error(f"{doc_id}: {digital_path.name} yok")
            continue
        text = _extract_text(digital_path)

        if banners["all"] not in text:
            report.error(f"{doc_id}: DEMO banner metni bulunamadı (G1)")
        spec = SPECS[doc_id]
        if spec.family == "agreement" and banners["contracts"] not in text:
            report.error(f"{doc_id}: 'NOT A REAL CONTRACT' ibaresi yok (G1)")

        # Long names wrap across lines inside cover-table cells; a field label ("Taraflar",
        # "Parties") can end up captured as a leading word too. Normalize whitespace and,
        # like validate_ledger.py's check_names, accept a match that merely *ends with* a
        # whitelisted name (the wrapped/label-prefixed case) rather than equalling it.
        whitelist = raws["company"]["name_whitelist"]
        normalized = re.sub(r"\s+", " ", text)
        # The `.watermark` div (CSS `position: fixed`, base.html) is extracted by PyMuPDF as
        # a run of bare "DEMO" tokens per page — harmless page noise, but the whitelist scan
        # below would otherwise misread "DEMO DEMO DEMO DEMO <Word>" as a name-pattern match
        # whenever a title/heading happens to start with a name-suffix word (observed: a
        # document titled "Sigorta ..." — Phase 5.1). The real banner ("DEMO / FICTIONAL
        # DOCUMENT ...", checked above) is a single non-repeated "DEMO" and is unaffected.
        normalized = re.sub(r"(?:DEMO ){2,}", "", normalized)
        for match in _NAME_PATTERN.finditer(normalized):
            name = match.group(1)
            if name in whitelist or any(name.endswith(w) for w in whitelist):
                continue
            report.error(f"{doc_id}: whitelist dışı isim {name!r} (G2)")

        other_project = (
            "İzmir"
            if doc_id.startswith("DOC-ANK")
            else "Ankara"
            if doc_id.startswith("DOC-IZM")
            else None
        )
        if other_project and other_project in text:
            report.error(f"{doc_id}: '{other_project}' geçiyor — proje karışması (G3)")
        if "Bursa" in text:
            report.error(f"{doc_id}: 'Bursa' geçiyor (G3)")

        # Whitespace-insensitive: PyMuPDF returns one line per rendered line, so a fact
        # that wraps ("June\n30, 2023") is still the same printed fact (Phase 3.2c).
        flat_text = " ".join(text.split())
        for field_name, value in entry["key_facts_used"].items():
            if " ".join(str(value).split()) not in flat_text:
                report.error(
                    f"{doc_id}: key_facts_used[{field_name}]={value!r} PDF metninde yok (G4)"
                )

    return report


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_documents")
    parser.add_argument("--prose-only", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUT / "manifest.json")
    args = parser.parse_args(argv)

    report = validate_prose()
    if not args.prose_only:
        generated = validate_generated(args.manifest)
        report.errors.extend(generated.errors)
        report.warnings.extend(generated.warnings)

    for message in report.errors:
        print(f"ERROR {message}")
    for message in report.warnings:
        print(f"WARNING {message}")
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 0 if not report.errors else 1


if __name__ == "__main__":
    sys.exit(main())
