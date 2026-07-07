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
    logical_name: str | None = None
    version: int = 1
    parent_document_id: str | None = None
    previous_version_id: str | None = None
    owner_username: str = "admin"
    visibility: str = "private"
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
class DocumentPreview:
    document: DocumentRecord
    chunks: list[ChunkRecord]
    extracted_text: str
    total_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "extracted_text": self.extracted_text,
            "total_tokens": self.total_tokens,
        }


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
class SentenceSupport:
    sentence: str
    status: str
    best_overlap: int
    supporting_chunk_id: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VerificationResult:
    support_score: float
    unsupported_sentences: list[str]
    sentence_support: list[SentenceSupport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "support_score": self.support_score,
            "unsupported_sentences": self.unsupported_sentences,
            "sentence_support": [item.to_dict() for item in self.sentence_support],
        }


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
    sentence_support: list[SentenceSupport] = field(default_factory=list)
    refused: bool = False
    refusal_reason: str | None = None
    guarded: bool = False
    retrieved_documents: list[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [citation.to_dict() for citation in self.citations],
            "support_score": self.support_score,
            "unsupported_sentences": self.unsupported_sentences,
            "retrieval_trace": self.retrieval_trace.to_dict(),
            "sentence_support": [item.to_dict() for item in self.sentence_support],
            "refused": self.refused,
            "refusal_reason": self.refusal_reason,
            "guarded": self.guarded,
            "retrieved_documents": self.retrieved_documents,
            "latency_ms": self.latency_ms,
        }


@dataclass(slots=True)
class EvaluationSampleResult:
    category: str
    question: str
    expected_terms: list[str]
    expected_refusal: bool
    answer: str
    passed: bool
    refused: bool
    recall_at_5: float
    ndcg_at_5: float
    reciprocal_rank: float
    citation_correct: bool
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvaluationRun:
    id: str
    sample_count: int
    recall_at_5: float
    ndcg_at_5: float
    mrr: float
    answer_accuracy: float
    citation_correctness: float
    refusal_accuracy: float
    hallucination_rate: float
    avg_latency_ms: float
    estimated_model_calls: int
    notes: str
    samples: list[EvaluationSampleResult]
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sample_count": self.sample_count,
            "recall_at_5": self.recall_at_5,
            "ndcg_at_5": self.ndcg_at_5,
            "mrr": self.mrr,
            "answer_accuracy": self.answer_accuracy,
            "citation_correctness": self.citation_correctness,
            "refusal_accuracy": self.refusal_accuracy,
            "hallucination_rate": self.hallucination_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "estimated_model_calls": self.estimated_model_calls,
            "notes": self.notes,
            "samples": [sample.to_dict() for sample in self.samples],
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class VersionChange:
    change_type: str
    text: str
    document_id: str
    document_name: str
    version: int
    page: int
    section: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VersionComparison:
    base_document: DocumentRecord
    target_document: DocumentRecord
    added: list[VersionChange]
    removed: list[VersionChange]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_document": self.base_document.to_dict(),
            "target_document": self.target_document.to_dict(),
            "added": [item.to_dict() for item in self.added],
            "removed": [item.to_dict() for item in self.removed],
            "summary": self.summary,
        }


@dataclass(slots=True)
class ConflictFinding:
    topic: str
    document_a: str
    document_a_id: str
    statement_a: str
    page_a: int
    document_b: str
    document_b_id: str
    statement_b: str
    page_b: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConflictAnalysis:
    id: str
    document_count: int
    conflict_count: int
    findings: list[ConflictFinding]
    notes: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_count": self.document_count,
            "conflict_count": self.conflict_count,
            "findings": [finding.to_dict() for finding in self.findings],
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class AuditLogEntry:
    id: str
    actor: str
    action: str
    detail: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
