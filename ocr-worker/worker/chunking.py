"""Page-bounded chunking (ADR-008): ~800 words, 100-word overlap.

Called once per page's text — never concatenate text across pages before chunking. That is
what makes "chunks never cross a page boundary" hold structurally rather than by a runtime
check: a chunk can only ever contain words from the single page it was built from.

Word count, not a real tokenizer, approximates "~800 tokens" (see
docs/plans/PHASE_0_2_PLAN.md §4 for the trade-off this accepts — no acceptance criterion
depends on an exact token count).
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"\S+")


def chunk_page_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    words = _WORD_RE.findall(text)
    if not words:
        return []
    if len(words) <= size:
        return [" ".join(words)]

    step = size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(words):
        window = words[start : start + size]
        chunks.append(" ".join(window))
        start += step
    return chunks
