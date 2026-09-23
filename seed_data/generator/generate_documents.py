"""Deterministic PDF generation from the truth ledger + frozen prose (no LLM here).

    python -m seed_data.generator.generate_documents [--out DIR]

Renders every `generate_in_phase: "3.1"` ledger document to `seed_data/documents/` and
writes `manifest.json` — the only thing `app.cli seed-demo-documents` reads (ADR-013:
the backend never imports this package). Refuses to run if the ledger doesn't validate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pymupdf
import yaml
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from seed_data.generator import facts as facts_mod
from seed_data.generator.document_specs import SPECS, DocumentSpec
from seed_data.generator.validate_ledger import DEFAULT_MASTER, DEFAULT_QUESTIONS, validate

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
PROSE_DIR = Path(__file__).resolve().parent / "prose"
DEFAULT_OUT = REPO_ROOT / "seed_data" / "documents"

_TOKEN_RE = re.compile(r"\[\[(\w+)\]\]")
_SCAN_DPI = 200

_PROJECT_CODE = {"ANK": "ANK_RES", "IZM": "IZM_RES", "CO": None}

_FOOTER_TEXT = {
    "tr": "DEMO — sentetik demo belgesi — sayfa",
    "en": "DEMO — synthetic demo document — page",
}
_COVENANT_COLUMNS = {"en": ["Period", "DSCR", "Result"]}
_PRODUCTION_COLUMNS = {
    "tr": ["Ay", "Üretim (MWh)", "Kullanılabilirlik (%)", "Kapasite Faktörü (%)"]
}
_PENDING_COLUMNS = {"tr": ["Adım", "Beklenen"]}


class GenerationError(Exception):
    pass


def substitute(text: str, facts: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(1)
        if token not in facts:
            raise GenerationError(
                f"unknown placeholder [[{token}]] — no such fact for this document"
            )
        return facts[token]

    return _TOKEN_RE.sub(repl, text)


def substitute_sections(
    raw_sections: list[dict[str, Any]], facts: dict[str, str]
) -> list[dict[str, Any]]:
    sections = []
    for section in raw_sections:
        sections.append(
            {
                "heading": substitute(section["heading"], facts),
                "paragraphs": [substitute(p, facts) for p in section.get("paragraphs", [])],
                "table": None,
            }
        )
    return sections


def _covenant_table(raws: dict[str, Any], language: str) -> dict[str, Any]:
    tests = raws["ankara_res"]["project"]["finance"]["covenant_tests"][-4:]
    rows = [
        [t["period"], facts_mod.format_value("dscr", t["dscr"], language), t["result"].capitalize()]
        for t in tests
    ]
    return {"columns": _COVENANT_COLUMNS[language], "rows": rows}


def _production_table(raws: dict[str, Any], language: str) -> dict[str, Any]:
    rows_data = raws["ankara_res"]["project"]["operations"]["monthly_production"][-6:]
    rows = [
        [
            r["month"],
            facts_mod.format_value("mwh", r["mwh"], language),
            facts_mod.format_percent(r["availability_pct"], language),
            facts_mod.format_percent(r["capacity_factor_pct"], language),
        ]
        for r in rows_data
    ]
    return {"columns": _PRODUCTION_COLUMNS[language], "rows": rows}


def _pending_steps_table(raws: dict[str, Any], language: str) -> dict[str, Any]:
    steps = raws["izmir_res"]["project"]["development"]["pending_steps"]
    rows = [[s["step"], s.get("expected") or "—"] for s in steps]
    return {"columns": _PENDING_COLUMNS[language], "rows": rows}


_TABLE_BUILDERS = {
    "covenant_tests": _covenant_table,
    "monthly_production": _production_table,
    "pending_steps": _pending_steps_table,
}


def _all_ledger_documents(raws: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for ledger_key in ("ankara_res", "izmir_res", "company"):
        for doc in raws[ledger_key]["documents"]:
            by_id[doc["id"]] = (ledger_key, doc)
    return by_id


def _nearest_generated(ref: str | None, by_id: dict[str, tuple[str, dict[str, Any]]]) -> str | None:
    seen: set[str] = set()
    while ref is not None and ref not in seen:
        seen.add(ref)
        _, doc = by_id[ref]
        if doc["generate_in_phase"] == "3.1":
            return ref
        ref = doc.get("supersedes")
    return None


def _revision_rows(
    doc: dict[str, Any], raws: dict[str, Any], facts: dict[str, str]
) -> list[dict[str, str]]:
    chain = raws["ankara_res"]["project"]["finance"]["facility_chain"]
    by_id = _all_ledger_documents(raws)
    rows = []
    for ref in chain:
        _, chain_doc = by_id[ref]
        if chain_doc["generate_in_phase"] != "3.1":
            continue
        language = chain_doc["language"]
        rows.append(
            {
                "version": chain_doc["version"],
                "date": facts_mod.format_date(chain_doc["document_date"]["value"], language),
                "status": facts_mod.STATUS_LABELS[language][chain_doc["status"]],
                "doc_no": ref,
            }
        )
    return rows


def _version_number(doc_id: str, raws: dict[str, Any]) -> int:
    chain = raws["ankara_res"]["project"]["finance"]["facility_chain"]
    return chain.index(doc_id) + 1 if doc_id in chain else 1


def _filename(doc: dict[str, Any], suffix: str = "") -> str:
    project = _PROJECT_CODE[doc["id"].split("-")[1]] or "COMPANY"
    date_str = doc["document_date"]["value"].isoformat()
    type_slug = re.sub(r"\s+", "_", doc["type"].strip())
    return f"{date_str}_{project}_{type_slug}_{doc['version']}_{doc['status']}{suffix}.pdf"


def _render_pdf(
    *, template_name: str, context: dict[str, Any], out_path: Path, env: Environment
) -> None:
    template = env.get_template(template_name)
    html = template.render(**context)
    HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf(str(out_path))


def _rasterize(source_pdf: Path, out_path: Path) -> None:
    """Rebuild `source_pdf` with a text-free image per page (ADR-006: `--skip-text`
    assumes exactly this) — same approach as `seed_data/t0/generate.py`."""
    source = pymupdf.open(source_pdf)
    scanned = pymupdf.open()
    for page in source:
        pixmap = page.get_pixmap(dpi=_SCAN_DPI)
        jpeg_bytes = pixmap.tobytes("jpeg", jpg_quality=85)
        image_page = scanned.new_page(width=pixmap.width, height=pixmap.height)
        image_page.insert_image(image_page.rect, stream=jpeg_bytes)
    scanned.save(out_path, deflate=True)
    scanned.close()
    source.close()


def _build_document(
    doc: dict[str, Any],
    raws: dict[str, Any],
    by_id: dict[str, tuple[str, dict[str, Any]]],
    env: Environment,
    out_dir: Path,
) -> dict[str, Any]:
    doc_id = doc["id"]
    spec: DocumentSpec | None = SPECS.get(doc_id)
    if spec is None:
        raise GenerationError(f"{doc_id}: no DocumentSpec in document_specs.py")
    language = doc["language"]
    facts = facts_mod.build_facts(doc, raws)

    prose_path = PROSE_DIR / f"{doc_id}.yaml"
    if not prose_path.exists():
        raise GenerationError(f"{doc_id}: prose/{doc_id}.yaml missing — run `make prose` first")
    prose = yaml.safe_load(prose_path.read_text(encoding="utf-8"))
    sections = substitute_sections(prose["sections"], facts)

    if spec.extra_table is not None:
        table = _TABLE_BUILDERS[spec.extra_table.kind](raws, language)
        heading = spec.extra_table.heading_tr if language == "tr" else spec.extra_table.heading_en
        sections.append({"heading": heading, "paragraphs": [], "table": table})

    revision_rows = _revision_rows(doc, raws, facts) if spec.has_revision_history else []
    signature_roles = [
        substitute(role, facts)
        for role in (spec.signature_roles_tr if language == "tr" else spec.signature_roles_en)
    ]
    subject_label = substitute(spec.subject_label_tr, facts) if spec.family == "letter" else ""
    subtitle = spec.subtitle_tr if language == "tr" else spec.subtitle_en

    context = {
        "facts": facts,
        "subtitle": subtitle,
        "banner_lines": _banner_lines(raws, spec.family),
        "sections": sections,
        "revision_rows": revision_rows,
        "signature_roles": signature_roles,
        "reference_label": spec.reference_label_tr,
        "subject_label": subject_label,
        "footer_text": _FOOTER_TEXT[language],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    digital_path = out_dir / _filename(
        doc, suffix=".digital" if doc["source_type"] == "scanned_pdf" else ""
    )
    _render_pdf(
        template_name=f"{spec.family}.html", context=context, out_path=digital_path, env=env
    )

    expected_pages = 1 + (1 if revision_rows else 0) + len(sections) + 1
    with pymupdf.open(digital_path) as rendered:
        if rendered.page_count != expected_pages:
            raise GenerationError(
                f"{doc_id}: rendered {rendered.page_count} pages, expected {expected_pages} "
                "(prose paragraph overflowed a page — shorten it)"
            )

    page_map: dict[str, int] = {"cover": 1}
    page = 2
    if revision_rows:
        page_map["__revision_history__"] = page
        page += 1
    for section in sections:
        page_map[section["heading"]] = page
        page += 1
    page_map["__signatures__"] = page

    served_file = digital_path.name
    digital_file: str | None = None
    if doc["source_type"] == "scanned_pdf":
        served_path = out_dir / _filename(doc)
        _rasterize(digital_path, served_path)
        served_file = served_path.name
        digital_file = digital_path.name

    supersedes_ref = _nearest_generated(doc.get("supersedes"), by_id)
    related_refs = [r for r in doc.get("related", []) if by_id[r][1]["generate_in_phase"] == "3.1"]
    project_code = _PROJECT_CODE[doc_id.split("-")[1]]

    return {
        "external_ref": doc_id,
        "file": served_file,
        "digital_file": digital_file,
        "title": facts["title"],
        "document_type": doc["type"],
        "department": doc["department"],
        "subdepartment": doc["subdepartment"],
        "project_code": project_code,
        "counterparty": facts["counterparty"],
        "document_date": doc["document_date"]["value"].isoformat(),
        "effective_date": doc["effective_date"]["value"].isoformat()
        if doc.get("effective_date")
        else None,
        "status": doc["status"],
        "version_label": doc["version"],
        # DB `documents.version` (int): position in the 6-link facility chain (1-6), or 1
        # for anything outside that chain (docs/plans/PHASE_3_1_PLAN.md §4.2).
        "version_number": _version_number(doc_id, raws),
        "supersedes_ref": supersedes_ref,
        "related_refs": related_refs,
        "tags": [project_code or "COMPANY", doc["version"]],
        "language": language,
        "confidentiality": doc["confidentiality"],
        "source_type": doc["source_type"],
        "page_count": expected_pages,
        "page_map": page_map,
        "facts_used": facts,
        # Subset actually resolved from `key_facts` (short, single-line values) — G4 checks
        # only these; `facts_used`'s cover-page strings (e.g. `parties_list`) can legitimately
        # line-wrap in the rendered PDF, which would break a naive substring check.
        "key_facts_used": {name: facts[name] for name in doc.get("key_facts", {})},
    }


def _banner_lines(raws: dict[str, Any], family: str) -> list[str]:
    banners = raws["company"]["demo_banners"]
    lines = [banners["all"]]
    if family == "agreement":
        lines.append(banners["contracts"])
    return lines


def generate(out_dir: Path = DEFAULT_OUT) -> list[dict[str, Any]]:
    report, _ = validate(DEFAULT_MASTER, DEFAULT_QUESTIONS)
    if report.error_count:
        for issue in report.issues:
            print(issue.render(), file=sys.stderr)
        raise GenerationError(
            f"ledger does not validate ({report.error_count} error(s)) — fix before generating"
        )

    raws = facts_mod.load_raws()
    by_id = _all_ledger_documents(raws)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

    entries = []
    for doc_id, (_, doc) in sorted(by_id.items()):
        if doc["generate_in_phase"] != "3.1":
            continue
        print(f"üretiliyor: {doc_id} — {doc['name']['value']}")
        entries.append(_build_document(doc, raws, by_id, env, out_dir))

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "ledger_demo_today": raws["ankara_res"]["meta"]["demo_today"].isoformat()
        if isinstance(raws["ankara_res"]["meta"]["demo_today"], date)
        else raws["ankara_res"]["meta"]["demo_today"],
        "documents": entries,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"yazıldı: {manifest_path} ({len(entries)} belge)")
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate_documents")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        generate(args.out)
    except GenerationError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
