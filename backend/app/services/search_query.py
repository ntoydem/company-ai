"""Turn a natural-language (Turkish) question into a full-text search query (ADR-020).

`websearch_to_tsquery` ANDs terms by default, and Turkish question words ("güncel",
"nedir", "ilk") never occur in English contracts — so a verbatim question matches nothing.
The query built here ORs the remaining terms; `ts_rank` then ranks chunks matching more
terms higher. Lower-casing and stemming stay with Postgres (the `turkish` / `simple`
configurations), which keeps the query consistent with how the chunks were indexed.
"""

from __future__ import annotations

import re
import unicodedata

from app.services.search_glossary import expand_terms

# Possessive / case suffixes written after an apostrophe: "RES'in", "covenant'ı".
_APOSTROPHE_SUFFIX = re.compile(r"['’]\S*")
_TOKEN = re.compile(r"[^\W_]+")

# Turkish question words, particles and conjunctions that carry no search signal. The
# Postgres `turkish` configuration keeps most of them (it stems "nedir" to "ne").
QUESTION_STOPWORDS = frozenset(
    {
        "acaba",
        "bir",
        "bu",
        "da",
        "de",
        "gibi",
        "göre",
        "hangi",
        "hangisi",
        "ile",
        "için",
        "ise",
        "kaç",
        "kaçtı",
        "kaçtır",
        "ki",
        "kim",
        "kimdir",
        "lütfen",
        "mi",
        "midir",
        "mu",
        "mudur",
        "mü",
        "müdür",
        "mı",
        "mıdır",
        "nasıl",
        "ne",
        "neden",
        "nedir",
        "neler",
        "nelerdir",
        "nerede",
        "neydi",
        "niçin",
        "o",
        "olan",
        "olarak",
        "var",
        "ve",
        "veya",
        "yok",
        "şey",
        "şu",
    }
)


def turkish_lower(text: str) -> str:
    """Locale-independent Turkish lower-casing (`str.lower` maps "I" to "i", not "ı")."""
    return text.replace("İ", "i").replace("I", "ı").lower()


_ASCII_FOLD_MAP = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"})


def turkish_fold(text: str) -> str:
    """`turkish_lower` plus ASCII-folding of the remaining Turkish letters, NFC-normalised
    first so a decomposed accent doesn't escape the fold (ADR-033). For *matching* a user's
    possibly ASCII-only or differently-cased spelling against a known name (project name
    words) — never for FTS query text, which stays as typed (Postgres's `turkish`
    configuration handles accents there)."""
    return turkish_lower(unicodedata.normalize("NFC", text)).translate(_ASCII_FOLD_MAP)


def build_search_query(question: str) -> str:
    """Return a `websearch_to_tsquery` string ("a OR b OR c"), or "" when nothing is left.

    Question terms first, then the glossary's document-side terms (Phase 3.2b): a Turkish
    "finansman" question also ORs `financing`/`facility`/`loan`, so the English page that
    actually states the figure can rank. Nothing is expanded when no term is known."""
    terms = question_terms(question)
    if not terms:
        return ""
    return " OR ".join(terms + expand_terms([turkish_lower(t) for t in terms]))


def question_terms(question: str) -> list[str]:
    """The question's own search-bearing tokens (original spelling, apostrophe suffixes
    stripped, stopwords and duplicates dropped) — the first half of `build_search_query`,
    also used by the assist block (ADR-027) to tell which terms found nothing."""
    cleaned = _APOSTROPHE_SUFFIX.sub("", question)
    terms: list[str] = []
    seen: set[str] = set()
    for token in _TOKEN.findall(cleaned):
        key = turkish_lower(token)
        if len(key) < 2 or key in QUESTION_STOPWORDS or key in seen:
            continue
        seen.add(key)
        terms.append(token)
    return terms
