from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class UserAccount:
    username: str
    full_name: str
    role: str
    hashed_password: str


@dataclass(slots=True)
class DocumentRecord:
    id: str
    filename: str
    content_type: str
    checksum: str
    source_path: str
    status: str
    page_count: int
    chunk_count: int
    error_message: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChunkRecord:
    id: str
    document_id: str
    document_name: str
    text: str
    page: int
    section: str
    token_count: int
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalHit:
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    page: int
    section: str
    score: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Citation:
    chunk_id: str
    document_id: str
    document_name: str
    page: int
    section: str
    snippet: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VerificationResult:
    support_score: float
    unsupported_sentences: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QueryTrace:
    dense_hits: list[RetrievalHit]
    keyword_hits: list[RetrievalHit]
    fused_hits: list[RetrievalHit]
    reranked_hits: list[RetrievalHit]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dense_hits": [hit.to_dict() for hit in self.dense_hits],
            "keyword_hits": [hit.to_dict() for hit in self.keyword_hits],
            "fused_hits": [hit.to_dict() for hit in self.fused_hits],
            "reranked_hits": [hit.to_dict() for hit in self.reranked_hits],
        }


@dataclass(slots=True)
class QueryResult:
    answer: str
    citations: list[Citation]
    support_score: float
    unsupported_sentences: list[str]
    retrieval_trace: QueryTrace

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [citation.to_dict() for citation in self.citations],
            "support_score": self.support_score,
            "unsupported_sentences": self.unsupported_sentences,
            "retrieval_trace": self.retrieval_trace.to_dict(),
        }


@dataclass(slots=True)
class AuditLogEntry:
    id: str
    actor: str
    action: str
    detail: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
