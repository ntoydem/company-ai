"""Document-type families and the starter guide (B-28b, ADR-025).

BACKEND_GAPS §4.7.2: there is no fixed "fill these fields" form — what matters differs per
document; a per-company *guide* steers Balbal's judgement and the upload screen. The guide is
configuration the customer admin edits (`document_type_guide`), not data (never in the truth
ledger). This module holds the starter rows and the pure matching rule; the migration data step
and the demo seed build the same rows (one snapshot, tested).

Starter keys come from BACKEND_GAPS §4.7.2 (contract: effective date; amendment: which contract +
change tags; invoice: vendor + work) and from what the truth ledger already records per document
(`parties`, `key_facts` names). No figures here.
"""

from __future__ import annotations

import re
from typing import Any

OTHER_FAMILY = "other"
MAX_EXTRA_FIELDS = 20
EXTRA_PREFIX_LITERAL = "extra_fields."
EXTRA_KEY_MAX_LENGTH = 48
_KEY_RE = re.compile(r"[^a-z0-9_]+")

# BACKEND_GAPS §4.7.4 — change tags only on documents that alter another one; the list grows by
# a human decision (admin), never automatically.
DEFAULT_CHANGE_TAGS: tuple[tuple[str, str], ...] = (
    ("faiz-değişikliği", "Faiz değişikliği"),
    ("teminat-yapısı-değişikliği", "Teminat yapısı değişikliği"),
    ("vade-değişikliği", "Vade değişikliği"),
    ("kredi-tutarı-değişikliği", "Kredi tutarı değişikliği"),
    ("ödeme-planı-değişikliği", "Ödeme planı değişikliği"),
    ("finansal-taahhüt-değişikliği", "Finansal taahhüt değişikliği"),
    ("taraf-değişikliği", "Taraf değişikliği"),
    ("temettü-dağıtım-koşulu-değişikliği", "Temettü dağıtım koşulu değişikliği"),
    ("sigorta-şartı-değişikliği", "Sigorta şartı değişikliği"),
)


def _f(key: str, label: str, hint: str) -> dict[str, str]:
    return {"key": key, "label": label, "hint": hint}


# family → row. `type_patterns` are lower-case substrings matched against `documents.document_type`.
DEFAULT_GUIDE: tuple[dict[str, Any], ...] = (
    {
        "family": "contract",
        "label": "Sözleşme",
        "type_patterns": [
            "agreement",
            "contract",
            "sözleşme",
            "anlaşma",
            "pledge",
            "lease",
            "terms",
        ],
        "suggested_extra_fields": [
            _f("parties", "Taraflar", "Sözleşmenin tarafları, virgülle"),
            _f("contract_value", "Sözleşme bedeli", "Belgede yazan tutar; para birimiyle"),
            _f("currency", "Para birimi", "TRY / EUR / USD"),
            _f("expiry_or_tenor", "Süre / bitiş", "Vade ya da sona erme tarihi"),
            _f("governing_law", "Uygulanacak hukuk", "Belgede yazıyorsa"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["effective_date", "counterparty"],
        "prompt_hint": "Yürürlük tarihi ve taraflar bu türde kritiktir; belgede yazıyorsa aktar.",
    },
    {
        "family": "amendment",
        "label": "Tadil / değişiklik",
        "type_patterns": [
            "amendment",
            "tadil",
            "change order",
            "waiver",
            "zeyil",
            "ek protokol",
        ],
        "suggested_extra_fields": [
            _f("amends", "Hangi belgeyi değiştirir", "Değiştirdiği sözleşme/lisansın adı"),
            _f("changed_items", "Neyi değiştirir", "Özet değil, işaret: faiz, vade, teminat…"),
        ],
        "suggested_tags": [slug for slug, _ in DEFAULT_CHANGE_TAGS],
        "standard_fields_emphasis": ["supersedes_document_id", "effective_date"],
        "prompt_hint": (
            "En kritik bilgi hangi belgenin tadili olduğudur; değişiklik etiketleriyle işaretle."
        ),
    },
    {
        "family": "licence_permit",
        "label": "Lisans / izin / ruhsat",
        "type_patterns": [
            "lisans",
            "licence",
            "license",
            "önlisans",
            "ruhsat",
            "çed",
            "permit",
            "connection",
            "bağlantı",
        ],
        "suggested_extra_fields": [
            _f("authority", "Veren kurum", "EPDK, belediye, bakanlık…"),
            _f("licence_no", "Lisans / karar no", "Belgedeki numara"),
            _f("capacity_mw", "Kapasite (MW)", "Belgede yazıyorsa"),
            _f("valid_until", "Geçerlilik sonu", "Tarih"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["effective_date"],
        "prompt_hint": "Kurum, numara ve geçerlilik tarihi; kapasite yazıyorsa aktar.",
    },
    {
        "family": "report",
        "label": "Rapor / memo",
        "type_patterns": [
            "report",
            "rapor",
            "memo",
            "review",
            "plan",
            "summary",
            "tracking",
            "punch list",
            "monthly",
        ],
        "suggested_extra_fields": [
            _f("period", "Dönem", "Raporun kapsadığı dönem"),
            _f("prepared_by", "Hazırlayan", "Firma ya da birim"),
            _f("subject_asset", "Konu / varlık", "Hangi tesis, hangi konu"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["document_date"],
        "prompt_hint": "Dönem ve hazırlayan; rakamları özetleme, belge okunur.",
    },
    {
        "family": "resolution_minutes",
        "label": "Karar / tutanak",
        "type_patterns": [
            "resolution",
            "karar",
            "tutanak",
            "minutes",
            "approval",
            "onay",
        ],
        "suggested_extra_fields": [
            _f("meeting_date", "Toplantı tarihi", "Tarih"),
            _f("resolution_no", "Karar no", "Belgedeki numara"),
            _f("decision_subject", "Karar konusu", "Kısa"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["document_date"],
        "prompt_hint": "Toplantı tarihi ve karar numarası.",
    },
    {
        "family": "insurance",
        "label": "Sigorta",
        "type_patterns": [
            "insurance",
            "sigorta",
            "poliçe",
            "policy",
        ],
        "suggested_extra_fields": [
            _f("insurer", "Sigortacı", "Şirket adı"),
            _f("policy_no", "Poliçe no", "Belgedeki numara"),
            _f("coverage_period", "Teminat dönemi", "Başlangıç–bitiş"),
            _f("insured_asset", "Sigortalı varlık", "Tesis / ekipman"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["effective_date", "expiration_date"],
        "prompt_hint": "Poliçe numarası ve teminat dönemi.",
    },
    {
        "family": "correspondence",
        "label": "Yazışma",
        "type_patterns": [
            "notice",
            "yazı",
            "letter",
            "opinion",
            "görüş",
            "başvuru",
            "talep",
            "bildirim",
        ],
        "suggested_extra_fields": [
            _f("sender", "Gönderen", "Kurum / kişi"),
            _f("recipient", "Alıcı", "Kurum / kişi"),
            _f("reference_no", "Referans no", "Yazı sayısı"),
            _f("reply_due", "Cevap süresi", "Tarih, yazıyorsa"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["document_date", "counterparty"],
        "prompt_hint": "Gönderen, alıcı ve varsa cevap süresi.",
    },
    {
        "family": "invoice",
        "label": "Fatura",
        "type_patterns": [
            "fatura",
            "invoice",
        ],
        "suggested_extra_fields": [
            _f("work_description", "Hangi iş için", "Kısa"),
            _f("invoice_no", "Fatura no", "Belgedeki numara"),
            _f("amount", "Tutar", "Para birimiyle"),
            _f("currency", "Para birimi", "TRY / EUR / USD"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["counterparty", "document_date"],
        "prompt_hint": (
            "Çoğu zaman hangi firmanın hangi iş için kestiği yeter; yürürlük tarihi açılmaz."
        ),
    },
    {
        "family": "workbook",
        "label": "Excel / veri dosyası",
        "type_patterns": [
            "model",
            "budget",
            "production",
            "covenant report",
            "xlsx",
            "workbook",
            "tablo",
        ],
        "suggested_extra_fields": [
            _f("period", "Dönem", "Verinin kapsadığı dönem"),
            _f("data_scope", "Veri kapsamı", "Hangi proje / hangi kalemler"),
            _f("source_system", "Kaynak sistem", "Varsa"),
        ],
        "suggested_tags": [],
        "standard_fields_emphasis": ["document_date"],
        "prompt_hint": (
            "Formül içeriği yapılandırılmaz; hesabı sistem yapar. Dönem ve kapsam yeter."
        ),
    },
    {
        "family": OTHER_FAMILY,
        "label": "Diğer",
        "type_patterns": [],
        "suggested_extra_fields": [],
        "suggested_tags": [],
        "standard_fields_emphasis": [],
        "prompt_hint": "",
    },
)


def fold(text: str) -> str:
    """Case-insensitive comparison key: `casefold()` plus the Turkish dotted-İ fix
    ("İhale".casefold() keeps a combining dot that "ihale" lacks)."""
    return text.casefold().replace("i\u0307", "i")


def match_family(document_type: str | None, guides: list[dict[str, Any]]) -> str:
    """First guide (in the given order) whose pattern is a substring of the type, else `other`.
    Order matters: `amendment` is listed before `contract` is *not* needed — "Licence Amendment"
    matches `amendment` and `licence`; the most specific family must therefore come first in the
    stored rows (the starter order puts amendment after contract on purpose: "Facility Agreement
    Amendment" is a contract amendment → amendment wins because it is checked by `specificity`)."""
    if not document_type:
        return OTHER_FAMILY
    haystack = fold(document_type)
    best: tuple[int, str] | None = None
    for guide in guides:
        if not guide.get("is_active", True):
            continue
        for pattern in guide.get("type_patterns") or []:
            needle = fold(str(pattern))
            if needle and needle in haystack and (best is None or len(needle) > best[0]):
                best = (len(needle), str(guide["family"]))
    return best[1] if best else OTHER_FAMILY


def normalize_extra_key(raw: str) -> str | None:
    """`snake_case`, ascii letters/digits/underscore, 1–48 chars; None when nothing is left."""
    key = raw.strip().casefold()
    key = (
        key.replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ç", "c")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace(" ", "_")
        .replace("-", "_")
    )
    key = _KEY_RE.sub("", key).strip("_")
    key = re.sub(r"_+", "_", key)
    return key[:EXTRA_KEY_MAX_LENGTH] or None
