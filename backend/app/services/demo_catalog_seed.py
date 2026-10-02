"""Tag catalogue + document-type guide starter rows (B-28b). Same rows as migration 0014's
data step; "create if missing", never changes an existing row (admin owns them afterwards)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document_type_guide import DocumentTypeGuide
from app.models.tag_catalog import TagKind
from app.repositories import guide_repo, tag_repo
from app.services.type_family import DEFAULT_CHANGE_TAGS, DEFAULT_GUIDE

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoSeedResult:
    key: str
    created: bool


def ensure_demo_catalog(session: Session, settings: Settings) -> list[DemoSeedResult]:
    del settings
    results: list[DemoSeedResult] = []
    for slug, label in DEFAULT_CHANGE_TAGS:
        if tag_repo.get(session, slug) is not None:
            results.append(DemoSeedResult(key=f"tag:{slug}", created=False))
            continue
        tag_repo.create(session, slug=slug, label=label, kind=TagKind.change, created_by_id=None)
        results.append(DemoSeedResult(key=f"tag:{slug}", created=True))
    for guide in DEFAULT_GUIDE:
        if guide_repo.get(session, guide["family"]) is not None:
            results.append(DemoSeedResult(key=f"guide:{guide['family']}", created=False))
            continue
        session.add(
            DocumentTypeGuide(
                family=guide["family"],
                label=guide["label"],
                type_patterns=list(guide["type_patterns"]),
                suggested_extra_fields=list(guide["suggested_extra_fields"]),
                suggested_tags=list(guide["suggested_tags"]),
                standard_fields_emphasis=list(guide["standard_fields_emphasis"]),
                prompt_hint=guide["prompt_hint"],
            )
        )
        results.append(DemoSeedResult(key=f"guide:{guide['family']}", created=True))
    session.commit()
    # `created` is a reserved LogRecord attribute — never use it as an `extra` key.
    log.info(
        "demo catalog seeded",
        extra={"created_keys": [r.key for r in results if r.created]},
    )
    return results
