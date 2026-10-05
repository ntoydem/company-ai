"""Prompt construction and answer parsing for `/api/ask` (rules 2, 5 and 6; ADR-014).

The system prompt is the single source of truth; `docs/prompts/ANSWER_SYSTEM_PROMPT.md`
mirrors it for review and a test keeps the two identical.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from app.models.document import Document
from app.repositories.document_chunk_repo import RetrievedChunk
from app.services.search_query import turkish_lower
from app.services.temporal import expiration_note
from app.services.version_chain import ChainPosition

NO_ANSWER_TEXT = (
    "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için "
    "yeterli bilgi bulamadım."
)
NO_REASON_TEXT = "belgelerde sebep belirtilmemiş"
# Ü-3 (Balbal Anayasası v2.0, 01.10.2026): cross-project comparison is never produced; the
# values are still given, each with its own source, after this fixed sentence.
COMPARISON_NOTICE = (
    "Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır."
)
_NO_ANSWER_MARKER = "yeterli bilgi bulamadım"

_RULES = [
    '1. Yalnızca "KAYNAKLAR" bölümündeki metinlerden cevap ver. Kaynaklarda olmayan hiçbir '
    "rakamı, tarihi, ismi veya olayı yazma; genel bilginle boşluk doldurma.",
    "2. Kaynaklar soruyu güvenilir şekilde cevaplamaya yetmiyorsa, yalnızca şu cümleyi yaz ve "
    f"başka hiçbir şey ekleme:\n{NO_ANSWER_TEXT}\n"
    "Sorulan değer, tarih veya olay kaynakların herhangi birinde açıkça yazıyorsa kaynaklar "
    "yeterlidir — diğer kaynakların ilgisiz olması cevabı engellemez; o değeri, geçtiği kaynağı "
    "etiketleyerek yaz.",
    '3. Soru belirli bir projeyi (örneğin "İzmir RES") soruyorsa ve kaynaklar o projeyi '
    'anlatmıyorsa, benzer başka bir projenin (örneğin "Ankara RES") bilgisinden çıkarım '
    "yapma; 2. kuraldaki cümleyi yaz.",
    "4. Bilgi içeren her cümlenin sonuna kullandığın kaynağın etiketini yaz: [K1], [K2] gibi. "
    "Etiketsiz olgu cümlesi yazma. Yalnızca verilen etiketleri kullan.",
    '5. Zaman ve versiyon: her kaynağın başlığında "Zincir:" satırı vardır. Soru "güncel", '
    '"şu anki", "mevcut", "bugün" gibi şimdiki durumu soruyorsa GÜNCEL işaretli belgeyi '
    'esas al. Soru "ilk", "orijinal", "başlangıçta", "önceden" gibi geçmişi soruyorsa '
    "zincirin İLK HALKA işaretli belgesini esas al. Soruda zaman belirtilmemişse GÜNCEL "
    "belgeyi esas al. Bir tadil (amendment) yalnızca kendi yazdığı maddeleri değiştirir: "
    "sorulan değer GÜNCEL belgede geçmiyorsa, zincirde ondan önceki belgede yazan değer hâlâ "
    "geçerlidir — onu, geçtiği belgeyi etiketleyerek güncel değer olarak yaz. Bir değer "
    'sonradan değiştirilmişse bunu belirt: "Bu değer <belge adı> ile önceki <eski değer> '
    'seviyesinden değiştirilmiştir." Eski değer yanlış değildir; tarihsel değerdir.',
    '6. Yorum, tahmin, öneri, projeksiyon veya görüş yazma. "Neden?" sorularında yalnızca '
    "belgede yazan sebebi aktar. Sorunun konusu (örn. bir değerin değiştirildiği) "
    "kaynaklarda geçiyor ama sebebi açıklanmıyorsa, 2. kuraldaki cümleyi DEĞİL, şu cümleyi "
    f'kelimesi kelimesine yaz: "{NO_REASON_TEXT}". 2. kuraldaki cümle yalnızca konunun kendisi '
    "kaynaklarda hiç geçmiyorsa kullanılır.",
    "7. Kaynaklar İngilizce olsa bile Türkçe cevap ver. Sayıları kaynaktaki biçimde yaz "
    "(örneğin 1,20x), tarihleri GG.AA.YYYY biçiminde yaz. Kısa ve düz yaz; gerekmedikçe "
    "başlık veya madde işareti kullanma.",
    '8. Bugünün tarihi "BUGÜN" satırında verilir, yalnızca bağlam içindir. Kalan gün, süre '
    "doldu mu, kaç yıl geçti gibi tarih farkı hesaplarını SEN yapma. Bir kaynakta hazır "
    'hesaplanmış bir satır varsa (örn. "Süre: …") onu aynen aktar; yoksa bu hesap için '
    "veri yok demektir, kendi başına tarih çıkarımı yapma.",
    "9. Kaynaklardan birden fazlası aynı terim veya kavram için farklı bir tanım ya da "
    "açıklama veriyorsa (5. kuraldaki zincir/versiyon ilişkisi geçerli değilse), hepsini "
    "kendi kaynak etiketiyle ayrı ayrı yaz; birini diğerine tercih etme, hangisinin doğru "
    "olduğuna karar verme.",
    '10. Soru birden fazla projeyi (örneğin "Ankara RES" ve "İzmir RES") kapsıyorsa her '
    "projenin değerini kendi kaynak etiketiyle AYRI bir cümlede yaz. Projeler arasında "
    'karşılaştırma, sıralama, "hangisi daha …" yargısı, fark veya oran hesabı yapma. Soru '
    "açıkça karşılaştırma istiyorsa önce kelimesi kelimesine şu cümleyi yaz, sonra değerleri "
    f"ayrı ayrı ver:\n{COMPARISON_NOTICE}",
]

SYSTEM_PROMPT = (
    "Sen bir şirket bilgi asistanısın. Görevin, aşağıda verilen şirket kaynaklarında yazanı "
    "bulup aktarmaktır. Yorum yapmazsın.\n\nKURALLAR\n" + "\n".join(_RULES)
)


@dataclass(frozen=True)
class PromptSource:
    ref: str
    chunk: RetrievedChunk
    document: Document
    position: ChainPosition


def order_sources(
    chunks: list[RetrievedChunk],
    documents: dict[UUID, Document],
    chain: dict[UUID, ChainPosition],
) -> list[PromptSource]:
    """Current documents first, then retrieval rank; labels K1.. follow that order."""
    ordered = sorted(
        chunks, key=lambda c: (not chain[c.document_id].is_current, -c.rank, c.chunk_index)
    )
    return [
        PromptSource(
            ref=f"K{index}",
            chunk=chunk,
            document=documents[chunk.document_id],
            position=chain[chunk.document_id],
        )
        for index, chunk in enumerate(ordered, start=1)
    ]


def _fmt(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "-"


def describe_chain(position: ChainPosition) -> str:
    if position.is_current:
        label = (
            "GÜNCEL"
            if position.chain_length > 1 or position.has_predecessor
            else ("GÜNCEL (zincirde tek belge)")
        )
    elif position.is_initial and (position.has_successor or position.chain_length > 1):
        label = "İLK HALKA (güncel değil)"
    elif not position.in_force:
        label = "YÜRÜRLÜKTE DEĞİL"
    else:
        label = f"ESKİ HALKA {position.position}/{position.chain_length} (güncel değil)"

    relations: list[str] = []
    if position.supersedes_title:
        relations.append(f'"{position.supersedes_title}" belgesini değiştirir')
    elif position.has_predecessor:
        relations.append("erişiminiz olmayan önceki bir belgeyi değiştirir")
    if position.superseded_by_title:
        relations.append(f'"{position.superseded_by_title}" tarafından değiştirilmiş')
    elif position.has_successor:
        relations.append("erişiminiz olmayan bir belge tarafından değiştirilmiş")
    return label + (" — " + "; ".join(relations) if relations else "")


def describe_metadata(document: Any) -> str:
    """B-28b: counterparty, catalogue tags and staff/AI extra fields as one line, so Balbal
    answers with the same facts the uploader recorded (BACKEND_GAPS §4.7.3). Empty when the
    document carries none of them — older sources stay byte-identical."""
    parts: list[str] = []
    if getattr(document, "counterparty", None):
        parts.append(f"Muhatap: {document.counterparty}")
    tags = getattr(document, "tags", None) or []
    if tags:
        parts.append("Etiketler: " + ", ".join(tags))
    extra = getattr(document, "extra_fields", None) or {}
    if extra:
        parts.append(
            "Ek alanlar: "
            + "; ".join(f"{key}={entry.get('value', '')}" for key, entry in sorted(extra.items()))
        )
    return " | ".join(parts)


def format_source(source: PromptSource, today: date) -> str:
    document = source.document
    header = (
        f"[{source.ref}] Belge: {document.title} | Tarih: {_fmt(document.document_date)} | "
        f"Yürürlük: {_fmt(document.effective_date)} | Versiyon: {document.version} | "
        f"Durum: {document.status.value} | Sayfa: {source.chunk.page_number}"
    )
    metadata = describe_metadata(document)
    lines = [header, f"Zincir: {describe_chain(source.position)}"]
    # ADR-026: ready-made, code-computed — the model reads it, never recomputes it (rule 3/8).
    note = expiration_note(document, today)
    if note:
        lines.append(note)
    if metadata:
        lines.append(metadata)
    lines.append(source.chunk.text.strip())
    return "\n".join(lines)


def build_user_prompt(question: str, sources: list[PromptSource], today: date) -> str:
    blocks = "\n\n".join(format_source(source, today) for source in sources)
    return f"BUGÜN: {_fmt(today)}\n\nSORU: {question.strip()}\n\nKAYNAKLAR:\n{blocks}"


_BRACKET = re.compile(r"\[([^\]]*)\]")
_REF = re.compile(r"K(\d+)")


def parse_citations(answer: str) -> list[str]:
    """Unique `K<n>` labels in order of first appearance; tolerates `[K1, K2]`."""
    refs: list[str] = []
    for group in _BRACKET.findall(answer):
        for number in _REF.findall(group):
            ref = f"K{int(number)}"
            if ref not in refs:
                refs.append(ref)
    return refs


def is_no_answer(answer: str) -> bool:
    return _NO_ANSWER_MARKER in turkish_lower(" ".join(answer.split()))
