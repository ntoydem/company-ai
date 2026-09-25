"""`SPECS`: every document's structural plan, merged from the per-project/department
bucket files (Phase 5.1 — a single ~1200-line `document_specs.py` for 70 documents would
break CLAUDE.md's "no 400+ line files" rule). `DocumentSpec`/`ExtraTable` re-exported from
`_base.py` so `from seed_data.generator.document_specs import SPECS, DocumentSpec` keeps
working unchanged for every caller (`generate_documents.py`, `validate_documents.py`,
`generate_prose.py`)."""

from __future__ import annotations

from seed_data.generator.document_specs import (
    ankara_admin,
    ankara_development,
    ankara_epc,
    ankara_finance,
    ankara_legal,
    ankara_operations,
    company,
    izmir,
)
from seed_data.generator.document_specs._base import DocumentSpec, ExtraTable, Family

__all__ = ["SPECS", "DocumentSpec", "ExtraTable", "Family"]

_BUCKETS = (
    ankara_development,
    ankara_finance,
    ankara_epc,
    ankara_operations,
    ankara_legal,
    ankara_admin,
    izmir,
    company,
)

SPECS: dict[str, DocumentSpec] = {}
for _bucket in _BUCKETS:
    overlap = SPECS.keys() & _bucket.SPECS.keys()
    assert not overlap, f"duplicate document id(s) across document_specs buckets: {overlap}"
    SPECS.update(_bucket.SPECS)
del _bucket
