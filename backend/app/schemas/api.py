from __future__ import annotations

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
    error_message: str | None = None
    created_at: str
    updated_at: str


class ReindexResponse(BaseModel):
    message: str
    document: DocumentResponse


class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: str


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


class EvaluationResponse(BaseModel):
    id: str
    created_at: str
    sample_count: int
    retrieval_recall_at_5: float
    mrr: float
    ndcg_at_5: float
    answer_accuracy: float
    citation_accuracy: float
    refusal_accuracy: float
    hallucination_rate: float
    notes: str


class AuditLogResponse(BaseModel):
    id: str
    actor: str
    action: str
    detail: str
    created_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    benchmark_ready: bool
    model_provider: str
    generation_model: str
    embedding_model: str
    max_upload_size_mb: int
