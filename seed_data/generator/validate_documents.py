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
from seed_data.generator.generate_documents import _FOOTER_TEXT, _TOKEN_RE, DEFAULT_OUT, PROSE_DIR
from seed_data.generator.validate_ledger import _NAME_PATTERN

NUMBER_PATTERN = re.compile(r"\d{3,}")
CURRENCY_PATTERN = re.compile(r"\b(EUR|USD|TRY)\b|[€$₺]")

# Statik kapı (11.10.2026, Naci onaylı — SORU B): document_specs.py'deki başlıkların
# KENDİSİ LLM talimatı sızdırmasın (DOC-YSV-FIN-009 olayı — "(a Separate, Later, Partial
# Financing; Never Capex or Equity Here)" gibi 82 karakter/13-14 kelimelik talimatlar PDF'e
# basılmıştı). Eşik mevcut 195 başlıklık korpustan ölçüldü (en uzun meşru başlık 41 karakter/
# 6 kelime); kilitli — gevşetilmeyecek. Gerçek bir yönerge `DocumentSpec.prose_guidance_*`
# ile verilir, başlığa gömülmez.
MAX_HEADING_CHARS = 55
MAX_HEADING_WORDS = 8
_HEADING_IMPERATIVE_PATTERN = re.compile(r"\b(Never|Always|Must|Do not)\b", re.IGNORECASE)
_HEADING_META_COMMENT_PATTERN = re.compile(r"\([A-Z][a-zA-Z]*(?:\s[A-Z][a-zA-Z]*)*:\s")

# Bir belgede tek sayı formatı (SORU C, 11.10.2026): DOC-YSV-FIN-009'da bulundu — bir EN
# belgenin bazı sayıları (`facts.py`'nin dil-duyarlı `_format_money`'sinden geçen capex/
# equity/total_debt) "26,400,000" (doğru), ama serbest-metin bir ledger alanı
# (`repayment_profile`, `kind="text"`, dil-duyarlı formatlamadan GEÇMİYOR) "98.000" (TR
# biçimi, ledger'a öyle yazılmıştı) basıyordu. En az 3 hane × en az bir grup gerektirir —
# ondalık oranlarla ("1.15x", "%0,80") çakışmaz.
_TR_GROUPED_NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{3})+\b")
_EN_GROUPED_NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")


def check_number_format_consistency(doc_id: str, language: str, text: str) -> list[str]:
    errors: list[str] = []
    if language == "en":
        for match in _TR_GROUPED_NUMBER_PATTERN.finditer(text):
            errors.append(f"{doc_id}: EN belgede TR-biçimi (nokta-gruplu) sayı: {match.group()!r}")
    elif language == "tr":
        for match in _EN_GROUPED_NUMBER_PATTERN.finditer(text):
            errors.append(f"{doc_id}: TR belgede EN-biçimi (virgül-gruplu) sayı: {match.group()!r}")
    return errors


# Dil tutarlılık kapısı (11.10.2026, Naci onaylı): belgenin dili (spec/ledger `language`)
# ile render edilmiş metnin bağlaç/stopword dağılımı uyumlu mu. Yalnız kısa, dile özgü ve
# kısaltmalarla ÇARPIŞMAYAN bağlaçlar seçildi — "a"/"in"/"to"/"da"/"de" gibi 1-2 harfli
# kelimeler "A.Ş." gibi kısaltmalardan ("a" + "ş" olarak ayrışır) yanlış pozitif üretiyordu
# (ilk ölçümde TR belgelerde %75'e kadar çıktı). Eşik gerçek 84 belgelik korpustan ölçüldü:
# her iki yönde de gözlenen maksimum "yanlış dil" oranı 0.0 — 0.15 olarak kilitlendi (çok
# üstünde headroom). MIN_SIGNAL_WORDS: toplam bağlaç sayısı 3'ten azsa (gürültülü örnek,
# korpusta 1-2 hit'lik belgeler var) kapı atlanır.
TR_CONNECTOR_WORDS = {
    "ve",
    "ile",
    "için",
    "gibi",
    "olan",
    "olarak",
    "veya",
    "ancak",
    "üzere",
    "tarafından",
}
EN_CONNECTOR_WORDS = {
    "the",
    "and",
    "this",
    "that",
    "shall",
    "will",
    "agreement",
    "pursuant",
    "hereby",
}
_WORD_PATTERN = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]+")
MIN_SIGNAL_WORDS = 3
MAX_WRONG_LANGUAGE_RATIO = 0.15


def check_language_consistency(doc_id: str, language: str, text: str) -> list[str]:
    words = (w.lower() for w in _WORD_PATTERN.findall(text))
    tr_count = 0
    en_count = 0
    for word in words:
        if word in TR_CONNECTOR_WORDS:
            tr_count += 1
        elif word in EN_CONNECTOR_WORDS:
            en_count += 1
    total = tr_count + en_count
    if total < MIN_SIGNAL_WORDS:
        return []
    if language == "en":
        ratio = tr_count / total
        wrong_label = "TR"
    elif language == "tr":
        ratio = en_count / total
        wrong_label = "EN"
    else:
        return []
    if ratio > MAX_WRONG_LANGUAGE_RATIO:
        return [
            f"{doc_id}: dil tutarsızlığı — {language} belgede {wrong_label} bağlaç oranı "
            f"{ratio:.2f} (eşik {MAX_WRONG_LANGUAGE_RATIO})"
        ]
    return []


# İş Emri 2026-10-11 Adım 1: aynı cümlede SPV adı 2 kez + bir bağlaç kelimesi geçerse
# (örn. "X ile X arasında" / "between X and X") kendiyle-sözleşme cümlesi şüphesi — bu
# ikili binary bir koşul (eşik yok, her ikisi de sağlanmalı); "A.Ş."/"Ltd." gibi
# kısaltmalardan sonraki noktada BÖLME YAPILMAZ (lookbehind korumalı).
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<!Ş)(?<!Ltd)(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])")
_SELF_REFERENCE_CONNECTORS = {"ile", "ve", "arasında", "between", "and", "with"}


def _body_only(text: str, language: str) -> str:
    """Kapak sayfası (başlık/alt başlık/banner/Taraflar tablosu) atlanır — SPV adının
    orada normal şekilde 1-2 kez geçmesi kendiyle-sözleşme anlamına gelmez; bu kapı
    yalnız GÖVDE metnindeki (sayfa 2+) cümleleri tarar."""
    marker = _FOOTER_TEXT.get(language)
    if marker is None:
        return text
    first_footer_end = text.find(marker)
    if first_footer_end == -1:
        return text
    newline = text.find("\n", first_footer_end)
    return text[newline + 1 :] if newline != -1 else ""


def check_self_referential_sentences(doc_id: str, spv_name: str, text: str) -> list[str]:
    errors: list[str] = []
    for sentence in _SENTENCE_SPLIT_PATTERN.split(text):
        if sentence.count(spv_name) < 2:
            continue
        words = set(_WORD_PATTERN.findall(sentence.lower()))
        hit = words & _SELF_REFERENCE_CONNECTORS
        if hit:
            snippet = sentence.strip().replace("\n", " ")[:150]
            errors.append(
                f"{doc_id}: aynı cümlede '{spv_name}' 2 kez + bağlaç {sorted(hit)}: {snippet!r}"
            )
    return errors


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


def check_heading_hygiene() -> list[str]:
    """`document_specs.py`'nin kendi `section_headings_tr/_en`'ini tarar (üretilmiş prose'a
    değil, Python-authored spec'e bakar — her `make lint`'te, prose hiç yoksa bile çalışır)."""
    errors: list[str] = []
    for doc_id, spec in SPECS.items():
        for lang, headings in (("tr", spec.section_headings_tr), ("en", spec.section_headings_en)):
            for heading in headings:
                if len(heading) > MAX_HEADING_CHARS:
                    errors.append(
                        f"{doc_id}: {lang} başlık {len(heading)} karakter "
                        f"(>{MAX_HEADING_CHARS}, talimat sızıntısı şüphesi): {heading!r}"
                    )
                if len(heading.split()) > MAX_HEADING_WORDS:
                    errors.append(
                        f"{doc_id}: {lang} başlık {len(heading.split())} kelime "
                        f"(>{MAX_HEADING_WORDS}, talimat sızıntısı şüphesi): {heading!r}"
                    )
                if _HEADING_IMPERATIVE_PATTERN.search(heading):
                    errors.append(
                        f"{doc_id}: {lang} başlıkta emir kipi talimat kelimesi: {heading!r}"
                    )
                if _HEADING_META_COMMENT_PATTERN.search(heading):
                    errors.append(
                        f"{doc_id}: {lang} başlıkta meta-yorum kalıbı (örn. 'Past Tense:'): "
                        f"{heading!r}"
                    )
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

        for error in check_number_format_consistency(doc_id, entry["language"], text):
            report.error(error)
        for error in check_language_consistency(doc_id, entry["language"], text):
            report.error(error)
        body_text = _body_only(text, entry["language"])
        for error in check_self_referential_sentences(doc_id, entry["parties"][0], body_text):
            report.error(error)

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
    for message in check_heading_hygiene():
        report.error(message)
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
