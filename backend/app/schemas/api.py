from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class DocumentResponse(BaseModel):
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
    created_at: str
    updated_at: str


class ReindexResponse(BaseModel):
    message: str
    document: DocumentResponse


class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: str


class UpdateDocumentPermissionsRequest(BaseModel):
    visibility: str = Field(pattern="^(private|public)$")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)


class RetrievalHitResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    page: int
    section: str
    score: float
    source: str


class CitationResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page: int
    section: str
    snippet: str
    score: float


class SentenceSupportResponse(BaseModel):
    sentence: str
    status: str
    best_overlap: int
    supporting_chunk_id: str | None = None
    reason: str | None = None


class QueryTraceResponse(BaseModel):
    dense_hits: list[RetrievalHitResponse]
    keyword_hits: list[RetrievalHitResponse]
    fused_hits: list[RetrievalHitResponse]
    reranked_hits: list[RetrievalHitResponse]


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    support_score: float
    unsupported_sentences: list[str]
    retrieval_trace: QueryTraceResponse
    sentence_support: list[SentenceSupportResponse] = []
    refused: bool = False
    refusal_reason: str | None = None
    guarded: bool = False
    retrieved_documents: list[str] = []
    latency_ms: float = 0.0


class EvaluationSampleResponse(BaseModel):
    category: str
    question: str
    expected_terms: list[str]
    expected_refusal: bool
    answer: str
    passed: bool
    refused: bool
    recall_at_5: float
    reciprocal_rank: float
    citation_correct: bool
    latency_ms: float


class EvaluationRunResponse(BaseModel):
    id: str
    sample_count: int
    recall_at_5: float
    mrr: float
    answer_accuracy: float
    citation_correctness: float
    refusal_accuracy: float
    hallucination_rate: float
    avg_latency_ms: float
    estimated_model_calls: int
    notes: str
    samples: list[EvaluationSampleResponse]
    created_at: str


class VersionChangeResponse(BaseModel):
    change_type: str
    text: str
    document_id: str
    document_name: str
    version: int
    page: int
    section: str


class VersionComparisonResponse(BaseModel):
    base_document: DocumentResponse
    target_document: DocumentResponse
    added: list[VersionChangeResponse]
    removed: list[VersionChangeResponse]
    summary: str


class ConflictFindingResponse(BaseModel):
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


class ConflictAnalysisResponse(BaseModel):
    id: str
    document_count: int
    conflict_count: int
    findings: list[ConflictFindingResponse]
    notes: str
    created_at: str


class AuditLogResponse(BaseModel):
    id: str
    actor: str
    action: str
    detail: str
    metadata: dict[str, Any] = {}
    created_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    model_provider: str
    generation_model: str
    embedding_model: str
    max_upload_size_mb: int
