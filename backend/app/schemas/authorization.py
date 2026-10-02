from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthorizationScope(BaseModel):
    """Optional narrowing of a query (department screen, project filter).

    Scope only ever *restricts* the allowed set; it never grants access.
    """

    model_config = ConfigDict(frozen=True)

    department: str | None = None
    project_id: UUID | None = None
    # B-28 (ADR-024): the default view is *published* documents only (retrieval, search,
    # `/api/ask`, the Excel catalogue). Document-handling endpoints (list/detail/download/
    # suggestion/inspect) pass True so the uploader sees their own pending document and the
    # target department's manager sees their review queue — still inside the single gate,
    # which adds only the pending documents that belong to the caller.
    include_pending: bool = False
