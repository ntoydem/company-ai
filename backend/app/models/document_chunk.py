import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, ForeignKey, Index, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

# bge-m3 output dimension (Phase 3.4); verify against the `embed` service when it lands.
EMBEDDING_DIM = 1024


class DocumentChunk(TimestampMixin, Base):
    """~800-token, page-bounded chunks (ADR-008) with dual-config FTS (ADR-007).

    `tsv_turkish`/`tsv_simple` are Postgres-generated columns (never written by the app):
    `turkish` applies stemming, `simple` is a safety net for English loanwords/codes that
    stemming could mangle (e.g. "DSCR"). Retrieval matches on either.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_chunk_index"
        ),
        Index("ix_document_chunks_tsv_turkish", "tsv_turkish", postgresql_using="gin"),
        Index("ix_document_chunks_tsv_simple", "tsv_simple", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int] = mapped_column(Integer)  # NOT NULL — ADR-008
    text: Mapped[str] = mapped_column(Text)
    tsv_turkish: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('turkish', text)", persisted=True)
    )
    tsv_simple: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', text)", persisted=True)
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
