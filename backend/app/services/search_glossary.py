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
