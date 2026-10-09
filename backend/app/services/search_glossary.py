"""Domain glossary for the FTS leg (Phase 3.2b, ADR-020 concretization).

Finance documents are English, legal/technical ones Turkish, questions are Turkish: a
question word like "finansman" never occurs on the English page that states the loan
amount, so lexical search cannot rank that page (Phase 4.1 report §3). Each entry maps a
Turkish query stem (prefix-matched against `turkish_lower`ed tokens) to the English
terms the documents actually use — and the reverse for English question words against
Turkish documents. Multi-word values become phrases in `websearch_to_tsquery`.

This is an energy-project-finance domain list, not a list of the golden questions'
words — `tests/test_search_glossary.py` uses the golden set only as a coverage check.
Extend it when a real document term is missing, never from a single question.
"""

from __future__ import annotations

# Turkish stem (prefix) -> document terms. Stems are lower-cased with `turkish_lower`.
GLOSSARY: dict[str, tuple[str, ...]] = {
    # finance
    "finansman": ("financing", "financial", "facility", "loan"),
    "kredi": ("loan", "facility", "debt", "financing"),
    "borç": ("debt", "outstanding"),
    "kalan": ("outstanding", "balance"),
    "ödenmemiş": ("outstanding",),
    "tutar": ("amount", "structured"),
    "faiz": ("interest", "rate"),
    "marj": ("margin",),
    "vade": ("tenor", "maturity", "years"),
    "tenor": ("tenor", "maturity"),
    "geri ödeme": ("repayment",),
    "taahhüt": ("covenant",),
    "covenant": ("covenant", "covenants", "coverage"),
    "dscr": ("dscr", "debt service coverage", "coverage ratio"),
    "kapanış": ("close", "closing"),
    "yerli banka": ("local bank", "bank"),
    "banka": ("bank", "lender"),
    "eca": ("export credit agency", "eca"),
    "ihracat kredi": ("export credit agency",),
    "temerrüt": ("default", "event of default"),
    "teminat": ("security", "collateral"),
    "tadil": ("amendment", "amended"),
    "değişiklik": ("amendment", "change order"),
    "sözleşme": ("agreement", "contract"),
    "anlaşma": ("agreement",),
    "bedel": ("price", "consideration", "contract price"),
    # 08.10.2026 (held-out dry run, HO-NEG-03): the EPC contract is English — "EPC Contractor",
    # "turnkey"; the Turkish question says "anahtar teslim müteahhit".
    "anahtar teslim": ("epc", "turnkey", "epc contractor"),
    "müteahhit": ("contractor", "epc contractor"),
    # energy / project
    "kapasite": ("capacity", "MW"),
    "kurulu güç": ("capacity", "installed capacity", "MW"),
    "üretim": ("generation", "production", "output"),
    "lisans": ("licence", "license"),
    "rapor": ("report",),
    "önlisans": ("pre-licence", "pre-license"),
    "yüklenici": ("contractor", "EPC"),
    "epc": ("epc", "contractor"),
    "inşaat": ("construction",),
    "geçici kabul": ("provisional acceptance",),
    "ticari işletme": ("commercial operation", "COD"),
    "cod": ("cod", "commercial operation"),
    "işletme": ("operation", "operating"),
    "devreye alma": ("commissioning",),
    "türbin": ("turbine",),
    # reverse: English question words -> Turkish document terms
    "licence": ("lisans",),
    "license": ("lisans",),
    "eia": ("çed",),
    "permit": ("ruhsat", "izin"),
    "land": ("arazi",),
}


def expand_terms(lowered: list[str]) -> list[str]:
    """Extra OR-terms for already `turkish_lower`ed question tokens (deduplicated,
    order-preserving). Prefix match ("finansmanında" -> "finansman"); multi-word keys
    are matched against the space-joined token sequence."""
    joined = " ".join(lowered)
    extra: list[str] = []
    seen: set[str] = set()
    for key, terms in GLOSSARY.items():
        matched = key in joined if " " in key else any(token.startswith(key) for token in lowered)
        if not matched:
            continue
        for term in terms:
            marker = term.lower()
            if marker in seen or marker in lowered:
                continue
            seen.add(marker)
            extra.append(f'"{term}"' if " " in term else term)
    return extra


# Adım 2 D2 (Tansu Ürün 1 §B, 08.10.2026): *concept* → the words that actually appear in
# document titles/types. `search_metadata` is an ILIKE over title/type/counterparty/tags, so a
# Turkish question word ("finansal model", "ödeme planı") never meets an English workbook
# title ("Financial Model 2026") unless it is expanded here. Values are plain substrings (no
# tsquery quoting); matching of keys follows `expand_terms` (prefix for one word, substring
# of the joined token sequence for multi-word keys). Kept in code (Naci, 08.10.2026);
# moving it to an admin table is a later job.
CONCEPT_GLOSSARY: dict[str, tuple[str, ...]] = {
    "finansal model": ("Financial Model", "Cashflow", "Debt", "DSCR"),
    "finansal": ("Financial",),
    "nakit akış": ("Cashflow", "Financial Model"),
    "ödeme planı": ("Financial Model", "Debt", "Repayment", "Ödeme Planı"),
    "geri ödeme": ("Repayment", "Financial Model"),
    "bütçe": ("Budget",),
    "sözleşme": ("Agreement", "Contract", "Sözleşme"),
    "kredi": ("Facility Agreement", "Loan", "Kredi"),
    "tadil": ("Amendment", "Tadil"),
    "lisans": ("Lisans", "Licence", "License"),
    "önlisans": ("Önlisans", "Pre-licence"),
    "sigorta": ("Sigorta", "Insurance"),
    "poliçe": ("Insurance", "Sigorta"),
    "teminat": ("Pledge", "Security", "Teminat", "Guarantee"),
    "rehin": ("Pledge",),
    "çed": ("ÇED",),
    "üretim": ("Production", "Üretim"),
    "rapor": ("Report", "Rapor"),
}


def concept_matches(lowered: list[str]) -> list[tuple[frozenset[str], tuple[str, ...]]]:
    """For `turkish_lower`ed question tokens: every CONCEPT_GLOSSARY key that applies, as
    (the tokens it covers, its title-side expansions). Multi-word keys cover each of their
    words that is present; one-word keys cover the tokens they prefix."""
    joined = " ".join(lowered)
    out: list[tuple[frozenset[str], tuple[str, ...]]] = []
    for key, expansions in CONCEPT_GLOSSARY.items():
        if " " in key:
            if key in joined:
                words = key.split()
                covered = frozenset(
                    token for token in lowered if any(token.startswith(w) for w in words)
                )
                out.append((covered, expansions))
        else:
            covered = frozenset(token for token in lowered if token.startswith(key))
            if covered:
                out.append((covered, expansions))
    return out


def metadata_terms(lowered: list[str]) -> list[str]:
    """Extra title-side search strings for `search_metadata` (deduplicated, order kept)."""
    out: list[str] = []
    for _covered, expansions in concept_matches(lowered):
        for term in expansions:
            if term not in out:
                out.append(term)
    return out


# ---------------------------------------------------------------- Ek-F (ADR-030) labels

# Ç-3 (Tansu A, 09.10.2026): when a question uses a term the glossary knows, the F-5 pattern
# opens with "«amendment» ifadesini tadil olarak anladım." — the Turkish label is code, the
# glossary is ours, so this is not "general knowledge" (Ç-6). Keys are glossary stems.
TR_LABEL: dict[str, str] = {
    "amendment": "tadil (değişiklik sözleşmesi)",
    "tadil": "tadil (amendment)",
    "covenant": "finansal taahhüt (covenant)",
    "dscr": "borç servisi karşılama oranı (DSCR)",
    "tenor": "vade",
    "eca": "ihracat kredi kurumu (ECA)",
    "cod": "ticari işletme tarihi (COD)",
    "epc": "anahtar teslim yüklenici sözleşmesi (EPC)",
    "licence": "lisans",
    "license": "lisans",
    "eia": "ÇED",
    "finansal model": "finansal model (Financial Model workbook'u)",
    "ödeme planı": "kredi geri ödeme planı (Financial Model, Debt sayfası)",
    "nakit akış": "nakit akış tablosu (Cashflow)",
    "bütçe": "bütçe / gerçekleşen (Budget)",
}

# F-5 "Aradığınız bilgi genellikle … belgesinde olur": the document type a concept usually
# lives in. Only known concepts; no match → the sentence is not written.
TYPICAL_DOCUMENT_TYPE: dict[str, str] = {
    "ödeme planı": "kredi sözleşmesinin geri ödeme maddesi ya da finansal model (Debt sayfası)",
    "geri ödeme": "kredi sözleşmesinin geri ödeme maddesi ya da finansal model (Debt sayfası)",
    "finansal model": "finansal model workbook'u",
    "nakit akış": "finansal model (Cashflow sayfası)",
    "bütçe": "bütçe / gerçekleşen raporu",
    "sigorta": "sigorta poliçesi ya da yenileme bildirimi",
    "poliçe": "sigorta poliçesi",
    "teminat": "teminat sözleşmesi (rehin, hisse rehni)",
    "lisans": "üretim lisansı ya da önlisans belgesi",
    "çed": "ÇED kararı ya da ÇED süreci yazısı",
    "tadil": "kredi sözleşmesi tadili (amendment)",
    "kredi": "kredi sözleşmesi (facility agreement)",
}


def understood_terms(lowered: list[str]) -> list[tuple[str, str]]:
    """`turkish_lower`ed question tokens → `(term as asked, Turkish label)` for every glossary
    stem the question uses, in question order, deduplicated by label. Multi-word stems match
    the joined token sequence; one-word stems prefix-match a token."""
    joined = " ".join(lowered)
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for stem, label in TR_LABEL.items():
        if " " in stem:
            if stem in joined and label not in seen:
                out.append((stem, label))
                seen.add(label)
            continue
        for token in lowered:
            if token.startswith(stem) and len(token) <= len(stem) + 4 and label not in seen:
                out.append((token, label))
                seen.add(label)
                break
    return out


def typical_document_type(lowered: list[str]) -> str | None:
    """The first TYPICAL_DOCUMENT_TYPE concept the question names, or None."""
    joined = " ".join(lowered)
    for concept, document_type in TYPICAL_DOCUMENT_TYPE.items():
        if " " in concept:
            if concept in joined:
                return document_type
        elif any(token.startswith(concept) for token in lowered):
            return document_type
    return None
