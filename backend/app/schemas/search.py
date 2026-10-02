"""`GET /api/search` (B-14, Aşama D): documents (content + metadata), projects and people in
one response. Documents come only from the caller's `allowed_document_ids` set."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.directory import DirectoryPerson
from app.schemas.document import DocumentListItem
from app.schemas.project import ProjectResponse

MatchedOn = Literal["content", "title", "type", "counterparty", "reference", "tag", "extra_field"]


class SearchDocumentHit(DocumentListItem):
    # Plain-text headline from the best-matching page (content hit); `None` when the
    # document matched on title/type/counterparty/external_ref only.
    snippet: str | None
    page_number: int | None
    # B-28b: what matched — content, or which metadata field (tag / extra field included).
    matched_on: MatchedOn = "content"


class SearchResponse(BaseModel):
    documents: list[SearchDocumentHit]
    projects: list[ProjectResponse]
    people: list[DirectoryPerson]
