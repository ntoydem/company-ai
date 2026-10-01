"""`GET /api/search` (B-14, Aşama D): documents (content + metadata), projects and people in
one response. Documents come only from the caller's `allowed_document_ids` set."""

from pydantic import BaseModel

from app.schemas.directory import DirectoryPerson
from app.schemas.document import DocumentListItem
from app.schemas.project import ProjectResponse


class SearchDocumentHit(DocumentListItem):
    # Plain-text headline from the best-matching page (content hit); `None` when the
    # document matched on title/type/counterparty/external_ref only.
    snippet: str | None
    page_number: int | None


class SearchResponse(BaseModel):
    documents: list[SearchDocumentHit]
    projects: list[ProjectResponse]
    people: list[DirectoryPerson]
