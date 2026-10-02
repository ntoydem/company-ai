"""`GET /api/search?q=&limit=` (B-14, Aşama D) — the top-bar search: document *content*
(the same FTS Balbal retrieves with, ADR-007/ADR-020) plus document metadata, projects and
people, in one call. Order of operations is the usual one: `allowed_document_ids` first,
then the search (kural 1). Search is not a question, so it writes no `audit_log` row
(ADR-016)."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.document import Document
from app.models.user import User
from app.repositories import document_chunk_repo, document_repo, project_repo, user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.schemas.directory import DirectoryPerson
from app.schemas.document import DocumentListItem
from app.schemas.project import ProjectResponse
from app.schemas.search import MatchedOn, SearchDocumentHit, SearchResponse
from app.services.authorization import allowed_document_ids
from app.services.search_query import build_search_query

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


def _metadata_match(document: Document, q: str) -> MatchedOn:
    """Which metadata field produced a non-content hit (B-28b `matched_on`), in the same
    priority order as `document_repo.search_metadata`'s OR clause."""
    needle = q.strip().casefold()
    if needle in document.title.casefold():
        return "title"
    if needle in document.document_type.casefold():
        return "type"
    if needle in document.counterparty.casefold():
        return "counterparty"
    if document.external_ref and needle in document.external_ref.casefold():
        return "reference"
    if any(needle in tag.casefold() for tag in document.tags or []):
        return "tag"
    return "extra_field"


@router.get("", response_model=SearchResponse)
def search(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SearchResponse:
    started = time.perf_counter()
    allowed = allowed_document_ids(
        current_user, AuthorizationScope(), SqlDocumentIdsProvider(session)
    )

    # Content hits: the glossary-expanded OR query Balbal uses (plan SORU 2), best page per
    # document, ranked. Metadata hits: raw `q`, title order, only to fill what content missed.
    hits = document_chunk_repo.search_document_hits(
        session, allowed_ids=allowed, query=build_search_query(q), limit=limit
    )
    hit_by_id = {hit.document_id: hit for hit in hits}
    metadata_only = [
        d
        for d in document_repo.search_metadata(session, allowed, q, limit=limit)
        if d.id not in hit_by_id
    ]
    content_docs = {d.id: d for d in document_repo.list_by_ids(session, list(hit_by_id))}
    documents: list[SearchDocumentHit] = []
    for hit in hits:
        document = content_docs.get(hit.document_id)
        if document is None:
            continue
        documents.append(
            SearchDocumentHit(
                **DocumentListItem.model_validate(document).model_dump(),
                snippet=hit.snippet,
                page_number=hit.page_number,
            )
        )
    for document in metadata_only:
        if len(documents) >= limit:
            break
        documents.append(
            SearchDocumentHit(
                **DocumentListItem.model_validate(document).model_dump(),
                snippet=None,
                page_number=None,
                matched_on=_metadata_match(document, q),
            )
        )

    projects = [ProjectResponse.model_validate(p) for p in project_repo.search(session, q)]
    people = [
        DirectoryPerson.from_user(person)
        for person in user_repo.search_directory(session, q=q, department_slug=None)
    ]
    log.info(
        "search",
        extra={
            "user_id": str(current_user.id),
            "q": q[:100],
            "documents": len(documents),
            "content_hits": len(hits),
            "projects": len(projects),
            "people": len(people),
            "duration_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    return SearchResponse(documents=documents, projects=projects, people=people)
