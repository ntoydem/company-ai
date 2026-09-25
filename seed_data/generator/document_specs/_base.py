"""Structural plan shared by every `document_specs/*.py` bucket file
(docs/plans/PHASE_3_1_PLAN.md §1.2/§2, docs/plans/PHASE_5_1_PLAN.md T5).

Everything here is Python-authored structure (section headings, table choices, signature
roles) — never a fact value. `generate_prose.py` asks the LLM to fill each heading with
placeholder-only paragraphs; `generate_documents.py` appends Python-built tables (no LLM
involved for numbers) and renders the whole thing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Family = Literal["agreement", "letter", "report"]


@dataclass(frozen=True)
class ExtraTable:
    heading_tr: str
    heading_en: str
    kind: Literal["covenant_tests", "monthly_production", "pending_steps"]


@dataclass(frozen=True)
class DocumentSpec:
    doc_id: str
    family: Family
    subtitle_tr: str
    subtitle_en: str
    section_headings_tr: list[str]
    section_headings_en: list[str]
    has_revision_history: bool = False
    extra_table: ExtraTable | None = None
    signature_roles_tr: list[str] = field(default_factory=list)
    signature_roles_en: list[str] = field(default_factory=list)
    reference_label_tr: str = "Sayı"
    subject_label_tr: str = "Konu"
