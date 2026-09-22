"""Turn a natural-language (Turkish) question into a full-text search query (ADR-020).

`websearch_to_tsquery` ANDs terms by default, and Turkish question words ("güncel",
"nedir", "ilk") never occur in English contracts — so a verbatim question matches nothing.
The query built here ORs the remaining terms; `ts_rank` then ranks chunks matching more
terms higher. Lower-casing and stemming stay with Postgres (the `turkish` / `simple`
configurations), which keeps the query consistent with how the chunks were indexed.
"""

from __future__ import annotations

import re

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


def build_search_query(question: str) -> str:
    """Return a `websearch_to_tsquery` string ("a OR b OR c"), or "" when nothing is left."""
    cleaned = _APOSTROPHE_SUFFIX.sub("", question)
    terms: list[str] = []
    seen: set[str] = set()
    for token in _TOKEN.findall(cleaned):
        key = turkish_lower(token)
        if len(key) < 2 or key in QUESTION_STOPWORDS or key in seen:
            continue
        seen.add(key)
        terms.append(token)
    return " OR ".join(terms)
