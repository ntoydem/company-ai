"""Assist block (ADR-027, Tansu Not 2): "veri yok" is a no-fabrication rule, not a no-help
rule. When a question cannot be answered, the fixed no-answer sentence stays the verdict
(ADR-014) and this module adds, **in code**, what can honestly be said about the user's
own corpus: which question terms matched nothing, which document-side terms exist for them
(glossary, verified against the user's allowed documents), which allowed documents are
available, and at most one short clarifying question.

Two paths, one rule each:
- zero retrieved chunks → no LLM at all (ADR-021); the clarifying question is a fixed
  template;
- chunks retrieved but the model declined → the model may append one `SORU:` line; code
  parses it and keeps it only if it carries no digits/dates/currency and names no document
  the user may not see. Anything else is dropped silently — the worst case is today's
  behaviour, never a chattier fabrication.

Every lookup runs inside `allowed` (ADR-004): `search_fts(allowed_ids=…)`,
`search_metadata(session, allowed, …)`. Nothing here can surface a document the gate hides.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.project import Project
from app.repositories import document_repo
from app.repositories.document_chunk_repo import RetrievedChunk, search_fts
from app.schemas.ask import AssistAvailableDocument, AssistAvailableGroup, AssistBlock
from app.services import tr_format
from app.services.answer_prompt import NO_DATA_VERDICT
from app.services.search_glossary import (
    GLOSSARY,
    concept_matches,
    expand_terms,
    metadata_terms,
    typical_document_type,
    understood_terms,
)
from app.services.search_query import question_terms, turkish_lower

log = logging.getLogger(__name__)

AssistKind = Literal["none", "clarify", "term_mismatch"]

MAX_AVAILABLE = 5
# ADR-030 (Ek-F F-3, EK_F_MODE): the list grows to 7 and keeps ≥ 3 places for documents that
# only *metadata* (title/type/concept) vouches for — chunk-vouched pages filled all 5 places
# before and pushed "Ankara RES ÇED Olumlu Kararı" out (ADIM1 DSC-007).
MAX_AVAILABLE_EKF = 7
CHUNK_QUOTA_EKF = 4
COMPANY_GROUP_NAME = "Şirket geneli"
MAX_UNDERSTOOD_TERMS = 2
MAX_CANDIDATE_TERMS = 5
MAX_QUESTION_CHARS = 200
# Shorter tokens ("RES", "kaç") are too common to say anything about a mismatch.
MIN_PROBE_TERM_CHARS = 3
# A metadata/"elimde şunlar var" hit must come from a term that actually narrows things:
# ≥ 4 characters ("RES" matches every project tag) and not matching more documents than
# we would list (a term found in > MAX_AVAILABLE documents is a non-term for this purpose).
MIN_SPECIFIC_TERM_CHARS = 4

# Words that stay in a question after the retrieval stopwords but carry no subject of
# their own ("zaman", "doluyor", "değeri"): their absence from the corpus says nothing
# about a terminology mismatch. Assist-side only — retrieval's query is untouched.
GENERIC_TERMS = frozenset(
    {
        "alındı",
        "alınmış",
        # Adım 2 D3 (08.10.2026, B ölçümü DSC-003/006/008/013): question verbs and filler
        # words that leaked into `term_mismatch` ("«demek», «biliyor», «musun» bulamadım").
        "biliyor",
        "biter",
        "bitecek",
        "bitiyor",
        "demek",
        "dosya",
        "dosyası",
        "hiç",
        "mevcut",
        "musun",
        "neler",
        "nerede",
        "peki",
        "yüklü",
        "asgari",
        "azami",
        "bedel",
        "bedeli",
        "belirtilen",
        "belirtilmiş",
        "bitmiş",
        "bitti",
        "bugün",
        "bunun",
        "değer",
        "değeri",
        "değişti",
        "değiştirdi",
        "dolar",
        "doldu",
        "dolmuş",
        "doluyor",
        "güncel",
        "ilk",
        "imzalanan",
        "imzalandı",
        "imzalanmış",
        "kadar",
        "kaçtı",
        "kimdir",
        "kurum",
        "kurumu",
        "kurumun",
        "maksimum",
        "minimum",
        "neye",
        "neyi",
        "oran",
        "oranları",
        "oranı",
        "son",
        "sonra",
        "sonucu",
        "sonuç",
        "sonuçları",
        "toplam",
        "tutar",
        "tutarı",
        "verildi",
        "yapıldı",
        "yıl",
        "yıllık",
        "zaman",
        "önce",
        "önceki",
        "şimdi",
        "şu",
    }
)
# A matched term is "specific" (it can vouch for an "elimde şunlar var" entry) only if it
# occurs in a modest share of the user's documents — "Ankara" is in most of them — and is
# long enough to carry a subject (R1: "sonucu"/"testi" vouched for unrelated pages).
SPECIFIC_MAX_DOC_SHARE = 0.25
SPECIFIC_MAX_DOCS = 10
MIN_VOUCH_TERM_CHARS = 5
# A model-written clarifying question that merely restates the user's question is dropped
# (R1: "İzmir RES projesine ait kredi faiz oranı nedir?" for "İzmir RES'in kredi faiz oranı
# nedir?") — it clarifies nothing. Share of the original's terms repeated in the model's.
ECHO_OVERLAP = 0.7

QUESTION_MARKER = "SORU:"
CLARIFY_TEMPLATE = "Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?"


def term_mismatch_template(unmatched: Iterable[str]) -> str:
    quoted = ", ".join(f"«{t}»" for t in unmatched)
    return (
        f"Şu ifadeyi belgelerde bu haliyle bulamadım: {quoted}. Ne demek istediğinizi açar mısınız?"
    )


# A clarifying question carries no facts: digits (hence dates, amounts, years), currency
# and percent signs are all refused. Matches the eval runner's G1 rule for this field.
_FACT_TOKEN = re.compile(r"[0-9€$₺%]")
_SENTENCE_END = re.compile(r"[.!?]")


@dataclass(frozen=True)
class AvailableDocument:
    document_id: UUID
    title: str
    document_type: str
    document_date: date
    project_code: str | None
    page_number: int | None


@dataclass(frozen=True)
class AvailableGroup:
    """F-3: one project's slice of `available` (Ü-3: projects are never mixed in one list)."""

    project_code: str | None
    project_name: str
    documents: tuple[AvailableDocument, ...]


@dataclass(frozen=True)
class Assist:
    kind: AssistKind = "none"
    question: str | None = None
    unmatched_terms: tuple[str, ...] = ()
    candidate_terms: tuple[str, ...] = ()
    available: tuple[AvailableDocument, ...] = ()
    # ADR-030: `available` grouped by project (EK_F_MODE only, else empty) and how many
    # further candidates were not listed — counted by code, never by the model (SORU 4).
    groups: tuple[AvailableGroup, ...] = ()
    more_count: int = 0
    # Why a model-written question was dropped (logged, never shown) — None when kept.
    dropped_reason: str | None = field(default=None, compare=False)


# ---------------------------------------------------------------- code-side lookups


def _available_card(document: Document, page_number: int | None) -> AvailableDocument:
    return AvailableDocument(
        document_id=document.id,
        title=document.title,
        document_type=document.document_type,
        document_date=document.document_date,
        project_code=document.project.code if document.project else None,
        page_number=page_number,
    )


def _metadata_probe_ok(term: str) -> bool:
    """Adım 2 D4: a title/type probe needs ≥ 4 characters — or a 3–5 letter upper-case
    acronym (ÇED, EPC, COD, DSCR), which `MIN_SPECIFIC_TERM_CHARS` alone kept out
    (B ölçümü DSC-007: "ÇED raporu nerede?" never reached the ÇED documents)."""
    return len(term) >= MIN_SPECIFIC_TERM_CHARS or (3 <= len(term) <= 5 and term.isupper())


def _concept_covered(session: Session, allowed: set[UUID], terms: list[str]) -> set[str]:
    """Adım 2 D2: lower-cased question tokens whose *concept* exists in the user's titles —
    "finansal"/"modeli" are not missing when an allowed "Financial Model 2026" exists."""
    lowered = [turkish_lower(t) for t in terms]
    covered: set[str] = set()
    for tokens, expansions in concept_matches(lowered):
        if any(
            document_repo.search_metadata(session, allowed, expansion, limit=1)
            for expansion in expansions
        ):
            covered |= tokens
    return covered


def unmatched_terms(session: Session, allowed: set[UUID], terms: list[str]) -> list[str]:
    """Question terms found nowhere the user may see — neither in a chunk (one LIMIT-1 FTS
    probe), nor in a title/type/tag (`search_metadata`), nor — through the concept glossary
    — as the Turkish name of a document the user's titles carry in English."""
    if not allowed:
        return []
    covered = _concept_covered(session, allowed, terms)
    out: list[str] = []
    for term in terms:
        if len(term) < MIN_PROBE_TERM_CHARS:
            continue
        if turkish_lower(term) in covered:
            continue
        if search_fts(session, allowed_ids=allowed, query=term, top_k=1):
            continue
        if _metadata_probe_ok(term) and document_repo.search_metadata(
            session, allowed, term, limit=1
        ):
            continue
        out.append(term)
    return out


def _glossary_known(lowered_terms: list[str]) -> set[str]:
    """Lower-cased question tokens covered by a glossary key — single-word keys by prefix
    ("vadesi" ← "vade"), multi-word keys ("ihracat kredi") by every word they contain."""
    joined = " ".join(lowered_terms)
    known: set[str] = set()
    for key in GLOSSARY:
        if " " in key:
            if key in joined:
                known.update(t for t in lowered_terms if any(t.startswith(w) for w in key.split()))
        else:
            known.update(t for t in lowered_terms if t.startswith(key))
    return known


def project_words(session: Session) -> set[str]:
    """Lower-cased words of every project name and code ("ankara", "res", "izm" …). A project
    the user has no documents for is not a *terminology* mismatch (R1: "İzmir" flagged for a
    finance user) — the question stays a `clarify`."""
    words: set[str] = set()
    for project in session.scalars(select(Project)).all():
        for raw in (project.name, project.code):
            words.update(w for w in re.split(r"[^\w]+", turkish_lower(raw)) if w)
    return words


def mismatch_terms(
    unmatched: list[str], all_terms: list[str] | None = None, *, excluded: set[str] | None = None
) -> list[str]:
    """The unmatched terms that *are* a terminology mismatch: at least four characters, not
    a generic question word, not a project name (`excluded`), and unknown to the glossary —
    a glossary-known word ("vade" → tenor) was already expanded into the retrieval query,
    so its equivalents either exist (then the question is answerable) or do not (then
    nothing is missing but the fact)."""
    lowered_all = [turkish_lower(t) for t in (all_terms or unmatched)]
    known = _glossary_known(lowered_all)
    skip = GENERIC_TERMS | (excluded or set())
    return [
        t
        for t in unmatched
        if len(t) >= MIN_SPECIFIC_TERM_CHARS
        and turkish_lower(t) not in skip
        and turkish_lower(t) not in known
    ]


def _can_be_specific(term: str) -> bool:
    """Five characters, or a 3–5 letter upper-case acronym (EPC, COD, DSCR); "RES" passes
    this test but fails the document-share cut, which is the point of having both."""
    return len(term) >= MIN_VOUCH_TERM_CHARS or (3 <= len(term) <= 5 and term.isupper())


def specific_matched_terms(
    session: Session, allowed: set[UUID], terms: list[str], unmatched: list[str]
) -> dict[str, set[UUID]]:
    """Matched terms that single documents out, with the documents they occur in. A term
    present in more than SPECIFIC_MAX_DOCS / SPECIFIC_MAX_DOC_SHARE of the allowed set
    ("Ankara", "RES") cannot vouch for an "elimde şunlar var" entry."""
    if not allowed:
        return {}
    limit = max(SPECIFIC_MAX_DOCS, int(len(allowed) * SPECIFIC_MAX_DOC_SHARE))
    out: dict[str, set[UUID]] = {}
    for term in terms:
        if not _can_be_specific(term) or term in unmatched:
            continue
        if turkish_lower(term) in GENERIC_TERMS:
            continue
        docs = {
            c.document_id for c in search_fts(session, allowed_ids=allowed, query=term, top_k=400)
        }
        for document in document_repo.search_metadata(session, allowed, term, limit=limit + 1):
            docs.add(document.id)
        if 0 < len(docs) <= limit:
            out[term] = docs
    return out


def candidate_terms(session: Session, allowed: set[UUID], unmatched: list[str]) -> list[str]:
    """Glossary document-side terms for the unmatched question terms, kept only when they
    really occur in an allowed document (a term the user cannot see is never suggested)."""
    if not allowed or not unmatched:
        return []
    out: list[str] = []
    for candidate in expand_terms([turkish_lower(t) for t in unmatched]):
        if len(out) >= MAX_CANDIDATE_TERMS:
            break
        if candidate in out:
            continue
        if search_fts(session, allowed_ids=allowed, query=candidate, top_k=1):
            out.append(candidate)
    return out


def available_from_metadata(
    session: Session,
    allowed: set[UUID],
    terms: list[str],
    *,
    limit: int = MAX_AVAILABLE,
    common_threshold: int = MAX_AVAILABLE,
) -> list[AvailableDocument]:
    """Allowed documents whose title/type/counterparty/tags/extra fields contain a question
    term (B-14's `search_metadata`, same gate). Deduplicated, ≤ `limit`; a term found in more
    than `common_threshold` documents points nowhere and is skipped. Order: documents whose
    *title* carries a question term first (ADR-030), then title."""
    if not allowed:
        return []
    by_id: dict[UUID, Document] = {}
    # Adım 2 D2/D4: the question's own terms (≥ 4 chars or an acronym) plus the concept
    # glossary's title-side words ("finansal model" → "Financial Model"), so English-titled
    # workbooks and Turkish questions meet. Still only `allowed` (G3), still ≤ MAX_AVAILABLE.
    probes = [t for t in terms if _metadata_probe_ok(t)]
    probes += [t for t in metadata_terms([turkish_lower(t) for t in terms]) if t not in probes]
    for term in probes:
        hits = document_repo.search_metadata(session, allowed, term, limit=common_threshold + 1)
        if len(hits) > common_threshold:
            continue  # too common to point anywhere (e.g. a project code carried by every tag)
        for document in hits:
            by_id.setdefault(document.id, document)
    lowered_probes = [turkish_lower(t) for t in probes]

    def title_hit(document: Document) -> int:
        title = turkish_lower(document.title)
        return 0 if any(p in title for p in lowered_probes) else 1

    ordered = sorted(by_id.values(), key=lambda d: (title_hit(d), d.title, d.id))[:limit]
    return [_available_card(document, None) for document in ordered]


_EXISTENCE_RE = re.compile(
    r"\b(var m[ıi]|yüklü m[üu]|mevcut m[uü]|nerede|neler|hangi dosya|hangisi|hangileri)\b",
    re.IGNORECASE,
)


def is_existence_question(text: str) -> bool:
    """Adım 2 D5: "X var mı / yüklü mü / nerede / neler" asks *whether and where* something
    exists — the answer is a list of the user's own documents, never a value."""
    return bool(_EXISTENCE_RE.search(turkish_lower(text)))


def available_from_chunks(
    documents: dict[UUID, Document], chunks: list[RetrievedChunk], *, limit: int = MAX_AVAILABLE
) -> list[AvailableDocument]:
    """ "Elimde şunlar var": the retrieved (hence allowed) documents, best page each, by
    retrieval rank, ≤ MAX_AVAILABLE — Ç-7.1 step 3, built from `retrieved_document_ids`
    and never from the model's text."""
    best: dict[UUID, RetrievedChunk] = {}
    for chunk in chunks:
        current = best.get(chunk.document_id)
        if current is None or chunk.rank > current.rank:
            best[chunk.document_id] = chunk
    ranked = sorted(best.values(), key=lambda c: (-c.rank, c.document_id))
    out: list[AvailableDocument] = []
    for chunk in ranked[:limit]:
        document = documents.get(chunk.document_id)
        if document is not None:
            out.append(_available_card(document, chunk.page_number))
    return out


# ---------------------------------------------------------------- the model's one line


def split_question_line(text: str) -> tuple[str, str | None]:
    """Separate the model's optional `SORU: …` line from its answer. Returns the answer
    without that line and the raw question (or None)."""
    kept: list[str] = []
    question: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if question is None and stripped.upper().startswith(QUESTION_MARKER):
            question = stripped[len(QUESTION_MARKER) :].strip()
            continue
        kept.append(line)
    return "\n".join(kept).strip(), question


def validate_question(
    question: str, *, hidden_titles: Iterable[str], original_question: str = ""
) -> tuple[str | None, str | None]:
    """Keep the model's clarifying question only if it is one short sentence ending in `?`,
    carries no digit/date/currency/percent, names no document outside the user's allowed
    set, and does not merely restate the user's question. Returns (question or None, drop
    reason or None)."""
    text = " ".join(question.split())
    if not text:
        return None, "empty"
    if len(text) > MAX_QUESTION_CHARS:
        return None, "too long"
    if not text.endswith("?"):
        return None, "not a question"
    if _SENTENCE_END.search(text[:-1]):
        return None, "more than one sentence"
    if _FACT_TOKEN.search(text):
        return None, "contains a number, date, currency or percent"
    lowered = turkish_lower(text)
    for title in hidden_titles:
        if len(title) >= 6 and turkish_lower(title) in lowered:
            return None, "names a document outside the allowed set"
    original = {turkish_lower(t) for t in question_terms(original_question) if len(t) >= 3}
    if original:
        repeated = {turkish_lower(t) for t in question_terms(text) if len(t) >= 3} & original
        if len(repeated) / len(original) >= ECHO_OVERLAP:
            return None, "echoes the question"
    return text, None


# ---------------------------------------------------------------- assembly


def _kind_for(mismatched: list[str]) -> AssistKind:
    """`term_mismatch` when the question uses a word the corpus and the glossary both lack;
    otherwise `clarify` (every word is known, the question still could not be answered)."""
    return "term_mismatch" if mismatched else "clarify"


def build_zero_chunk_assist(
    session: Session, allowed: set[UUID], question: str, *, ek_f: bool = False
) -> Assist:
    """Nothing retrieved: no LLM (ADR-021). Everything here is a lookup inside `allowed`."""
    terms = question_terms(question)
    unmatched = unmatched_terms(session, allowed, terms)
    mismatched = mismatch_terms(unmatched, terms, excluded=project_words(session))
    candidates = candidate_terms(session, allowed, unmatched)
    more = 0
    if ek_f:
        candidates_all = available_from_metadata(
            session, allowed, terms, limit=50, common_threshold=MAX_AVAILABLE
        )
        available = candidates_all[:MAX_AVAILABLE_EKF]
        more = len(candidates_all) - len(available)
    else:
        available = available_from_metadata(session, allowed, terms)
    kind = _kind_for(mismatched)
    text = term_mismatch_template(mismatched) if kind == "term_mismatch" else CLARIFY_TEMPLATE
    return Assist(
        kind=kind,
        question=text,
        unmatched_terms=tuple(mismatched),
        candidate_terms=tuple(candidates),
        available=tuple(available),
        groups=tuple(group_available(session, available, question)) if ek_f else (),
        more_count=more,
    )


def build_insufficient_assist(
    session: Session,
    allowed: set[UUID],
    question: str,
    *,
    documents: dict[UUID, Document],
    chunks: list[RetrievedChunk],
    model_question: str | None,
    ek_f: bool = False,
) -> Assist:
    """Chunks reached the prompt, the model still declined: list what was retrieved (code),
    detect unmatched terms (code), keep the model's one question only if it passes
    `validate_question`; otherwise fall back to the fixed template. With `ek_f` (ADR-030)
    the list is ≤ 7 with a quota: chunk-vouched documents take at most 4 places, metadata /
    concept matches get the rest (and spill back when there are fewer than 3)."""
    terms = question_terms(question)
    unmatched = unmatched_terms(session, allowed, terms)
    mismatched = mismatch_terms(unmatched, terms, excluded=project_words(session))
    candidates = candidate_terms(session, allowed, unmatched)
    # "Elimde şunlar var" = the retrieved documents that a *specific* question term vouches
    # for. Pages pulled in by generic tokens alone ("Ankara", "RES", "kaç") are not listed:
    # that would suggest the corpus knows the subject when it does not.
    specific = specific_matched_terms(session, allowed, terms, unmatched)
    vouched: set[UUID] = set().union(*specific.values()) if specific else set()
    vouched_chunks = [c for c in chunks if c.document_id in vouched]
    more = 0
    if ek_f:
        available, more = _quota_list(session, allowed, terms, documents, vouched_chunks)
    else:
        available = available_from_chunks(documents, vouched_chunks)
        # Adım 2 D1/D5: documents that have no chunks (workbooks) or that only a *concept* of
        # the question names never reach the prompt, so the chunk list misses them; add the
        # metadata matches (same gate) — always for an existence question, otherwise only
        # when the chunk list is empty. Chunk-vouched documents stay first.
        if is_existence_question(question) or not available:
            seen = {card.document_id for card in available}
            for card in available_from_metadata(session, allowed, terms):
                if card.document_id not in seen and len(available) < MAX_AVAILABLE:
                    available.append(card)
                    seen.add(card.document_id)
    kind = _kind_for(mismatched)
    kept: str | None = None
    reason: str | None = None
    if model_question is not None:
        kept, reason = validate_question(
            model_question,
            hidden_titles=document_repo.titles_outside(session, allowed),
            original_question=question,
        )
        if reason is not None:
            log.info("assist question dropped", extra={"reason": reason})
    text = kept or (
        term_mismatch_template(mismatched) if kind == "term_mismatch" else CLARIFY_TEMPLATE
    )
    return Assist(
        kind=kind,
        question=text,
        unmatched_terms=tuple(mismatched),
        candidate_terms=tuple(candidates),
        available=tuple(available),
        groups=tuple(group_available(session, available, question)) if ek_f else (),
        more_count=more,
        dropped_reason=reason,
    )


def _quota_list(
    session: Session,
    allowed: set[UUID],
    terms: list[str],
    documents: dict[UUID, Document],
    vouched_chunks: list[RetrievedChunk],
) -> tuple[list[AvailableDocument], int]:
    """ADR-030 F-3 quota. Returns (listed, how many more candidates exist). The "too common"
    probe threshold stays MAX_AVAILABLE (5): it is about a term's specificity, not the list
    size — at 7 the dry run let "Ankara"/"Report" (7 hits each) flood the metadata places
    and push "Financial Model 2026" / "Ankara RES ÇED Olumlu Kararı" into the surplus."""
    # A document the metadata vouches for takes a *metadata* place even when it also has
    # chunks — otherwise a low retrieval rank hides it behind generic report pages (dry run,
    # 09.10.2026: "Ankara RES ÇED Olumlu Kararı" ranked 10th of 12 chunk cards).
    meta_cards = available_from_metadata(
        session, allowed, terms, limit=50, common_threshold=MAX_AVAILABLE
    )
    meta_ids = {c.document_id for c in meta_cards}
    chunk_cards = [
        c
        for c in available_from_chunks(documents, vouched_chunks, limit=50)
        if c.document_id not in meta_ids
    ]
    meta_places = MAX_AVAILABLE_EKF - min(len(chunk_cards), CHUNK_QUOTA_EKF)
    shown_meta = meta_cards[:meta_places]
    shown_chunks = chunk_cards[: MAX_AVAILABLE_EKF - len(shown_meta)]
    listed = shown_meta + shown_chunks
    return listed, len(chunk_cards) + len(meta_cards) - len(listed)


# ---------------------------------------------------------------- Ek-F (ADR-030) rendering


def group_available(
    session: Session, available: list[AvailableDocument], question: str
) -> list[AvailableGroup]:
    """F-3: `available` by project. A project named in the question comes first, then by
    document count; company-level documents (no project) form the last group. Projects are
    read from the `projects` table; a code without a row keeps its code as name."""
    if not available:
        return []
    names = {p.code: p.name for p in session.scalars(select(Project)).all()}
    lowered_question = turkish_lower(question)
    by_code: dict[str | None, list[AvailableDocument]] = {}
    for card in available:
        by_code.setdefault(card.project_code, []).append(card)

    def named(code: str | None) -> int:
        if code is None:
            return 1
        words = [
            w for w in re.split(r"[^\w]+", turkish_lower(names.get(code, code))) if len(w) >= 3
        ]
        return 0 if any(w in lowered_question for w in words) else 1

    ordered = sorted(
        by_code.items(),
        key=lambda item: (named(item[0]), item[0] is None, -len(item[1]), str(item[0])),
    )
    return [
        AvailableGroup(
            project_code=code,
            project_name=names.get(code, code) if code is not None else COMPANY_GROUP_NAME,
            documents=tuple(sorted(cards, key=lambda c: (c.document_date, c.title), reverse=True)),
        )
        for code, cards in ordered
    ]


def render_no_data(assist: Assist, question: str) -> str:
    """F-5 (Ek-F): the text the user reads instead of NO_ANSWER_TEXT + assist block. Every
    line is code: the Ç-3 "anladım" sentence (glossary label), the fixed verdict, the F-3
    grouped list with document dates, "… ve N belge daha" (N counted here, SORU 4), the
    upload sentence only when nothing is listed and the typical document type is known, and
    the clarifying question as the last line (F-5: the answer always ends with a question or
    a choice)."""
    lowered = [turkish_lower(t) for t in question_terms(question)]
    lines: list[str] = []
    understood = understood_terms(lowered)[:MAX_UNDERSTOOD_TERMS]
    if understood:
        lines.append(
            " ".join(f"«{term}» ifadesini {label} olarak anladım." for term, label in understood)
        )
    lines.append(NO_DATA_VERDICT)
    if assist.available:
        lines.append("Elimde konuyla ilgili şunlar var:")
        for group in assist.groups or group_available_fallback(assist.available):
            items = "; ".join(
                f"{d.title} ({tr_format.format_date(d.document_date)})" for d in group.documents
            )
            lines.append(f"{group.project_name}: {items}")
        if assist.more_count > 0:
            lines.append(f"… ve {assist.more_count} belge daha.")
        lines.append("İsterseniz açayım.")
    else:
        lines.append("Elimde konuyla ilgili bir kayıt bulunmuyor.")
        typical = typical_document_type(lowered)
        if typical:
            lines.append(
                f"Aradığınız bilgi genellikle {typical} içinde olur; yüklenirse cevaplayabilirim."
            )
    lines.append(assist.question or CLARIFY_TEMPLATE)
    return "\n".join(lines)


def group_available_fallback(available: tuple[AvailableDocument, ...]) -> list[AvailableGroup]:
    """Grouping without a session (codes as names) — only when `groups` was not built."""
    by_code: dict[str | None, list[AvailableDocument]] = {}
    for card in available:
        by_code.setdefault(card.project_code, []).append(card)
    return [
        AvailableGroup(
            project_code=code,
            project_name=code if code is not None else COMPANY_GROUP_NAME,
            documents=tuple(cards),
        )
        for code, cards in sorted(by_code.items(), key=lambda i: (i[0] is None, str(i[0])))
    ]


# ---------------------------------------------------------------- wire / audit shapes


def assist_block(assist: Assist | None) -> AssistBlock | None:
    """`AskResponse.assist`: None stays None (ASSIST_MODE off, or an answered reply)."""
    if assist is None:
        return None
    return AssistBlock(
        kind=assist.kind,
        question=assist.question,
        unmatched_terms=list(assist.unmatched_terms),
        candidate_terms=list(assist.candidate_terms),
        available=[
            AssistAvailableDocument(
                document_id=a.document_id,
                title=a.title,
                document_type=a.document_type,
                document_date=a.document_date,
                project_code=a.project_code,
                page_number=a.page_number,
            )
            for a in assist.available
        ],
        groups=[
            AssistAvailableGroup(
                project_code=g.project_code,
                project_name=g.project_name,
                documents=[
                    AssistAvailableDocument(
                        document_id=a.document_id,
                        title=a.title,
                        document_type=a.document_type,
                        document_date=a.document_date,
                        project_code=a.project_code,
                        page_number=a.page_number,
                    )
                    for a in g.documents
                ],
            )
            for g in assist.groups
        ],
    )


def assist_json(assist: Assist | None) -> dict[str, Any] | None:
    """`audit_log.assist`: exactly what the user saw (rule 4), plus why a model question was
    dropped when it was — the eval and a later review read both."""
    block = assist_block(assist)
    if block is None or assist is None:
        return None
    payload: dict[str, Any] = block.model_dump(mode="json")
    if assist.dropped_reason is not None:
        payload["dropped_reason"] = assist.dropped_reason
    return payload
