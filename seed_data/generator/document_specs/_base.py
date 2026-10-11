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
    # Adım 5 PF-1 LLM üretim planı (11.10.2026): hangi ledger'dan okunacak — "covenant_tests"
    # kind'i başta yalnız Karatepe (ankara_res) için yazılmıştı (hardcoded); Yeşilova'nın
    # Annex F raporu aynı tabloyu PAYLAŞIYOR ama kendi verisiyle (SORU 4 kararı).
    ledger_key: str = "ankara_res"


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
    # Düzeltme (11.10.2026, Naci onaylı — SORU B): LLM'i yönlendirmek için başlığın
    # KENDİSİNE talimat gömme ihtiyacı (DOC-YSV-FIN-009 Yeşilova FA olayı — 82 karaktere
    # kadar çıkan parantez içi talimatlar PDF'e basıldı). Bu alan `generate_prose.py`'nin
    # LLM'e giden kullanıcı mesajına "Ek yönerge (belgeye YAZILMAYACAK)" olarak eklenir;
    # `generate_documents.py` BUNA HİÇ DOKUNMAZ — section_headings_* her zaman nötr ve
    # render edilen metin olarak kalır.
    prose_guidance_tr: str | None = None
    prose_guidance_en: str | None = None
    # Bir facts/key_facts anahtarını LLM'e hiç ÖNERMEZ (örn. "bu üretimde equity cümlesi
    # yazılmasın" — Tansu'nun cevabı beklenirken). `known_placeholders` doğrulaması hâlâ
    # kabul eder; yalnız teşvik edilmez (generate_prose.py::generate_one).
    prose_suppress_facts: frozenset[str] = field(default_factory=frozenset)
