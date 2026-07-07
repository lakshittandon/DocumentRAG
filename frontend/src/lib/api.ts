export interface TokenResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}

export interface DocumentRecord {
  id: string;
  filename: string;
  content_type: string;
  checksum: string;
  source_path: string;
  status: string;
  page_count: number;
  chunk_count: number;
  logical_name?: string | null;
  version: number;
  parent_document_id?: string | null;
  previous_version_id?: string | null;
  owner_username: string;
  visibility: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChunkPreview {
  id: string;
  document_id: string;
  document_name: string;
  text: string;
  page: number;
  section: string;
  token_count: number;
  source_path: string;
}

export interface DocumentPreview {
  document: DocumentRecord;
  chunks: ChunkPreview[];
  extracted_text: string;
  total_tokens: number;
}

export interface RetrievalHit {
  chunk_id: string;
  document_id: string;
  document_name: string;
  text: string;
  page: number;
  section: string;
  score: number;
  source: string;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page: number;
  section: string;
  snippet: string;
  score: number;
}

export interface QueryTrace {
  dense_hits: RetrievalHit[];
  keyword_hits: RetrievalHit[];
  fused_hits: RetrievalHit[];
  reranked_hits: RetrievalHit[];
}

export interface SentenceSupport {
  sentence: string;
  status: string;
  best_overlap: number;
  supporting_chunk_id?: string | null;
  reason?: string | null;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  support_score: number;
  unsupported_sentences: string[];
  retrieval_trace: QueryTrace;
  sentence_support: SentenceSupport[];
  refused: boolean;
  refusal_reason?: string | null;
  guarded: boolean;
  retrieved_documents: string[];
  latency_ms: number;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  detail: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface EvaluationSample {
  category: string;
  question: string;
  expected_terms: string[];
  expected_refusal: boolean;
  answer: string;
  passed: boolean;
  refused: boolean;
  recall_at_5: number;
  ndcg_at_5: number;
  reciprocal_rank: number;
  citation_correct: boolean;
  latency_ms: number;
}

export interface EvaluationRun {
  id: string;
  sample_count: number;
  recall_at_5: number;
  ndcg_at_5: number;
  mrr: number;
  answer_accuracy: number;
  citation_correctness: number;
  refusal_accuracy: number;
  hallucination_rate: number;
  avg_latency_ms: number;
  estimated_model_calls: number;
  notes: string;
  samples: EvaluationSample[];
  created_at: string;
}

export interface VersionChange {
  change_type: string;
  text: string;
  document_id: string;
  document_name: string;
  version: number;
  page: number;
  section: string;
}

export interface VersionComparison {
  base_document: DocumentRecord;
  target_document: DocumentRecord;
  added: VersionChange[];
  removed: VersionChange[];
  summary: string;
}

export interface ConflictFinding {
  topic: string;
  document_a: string;
  document_a_id: string;
  statement_a: string;
  page_a: number;
  document_b: string;
  document_b_id: string;
  statement_b: string;
  page_b: number;
  reason: string;
}

export interface ConflictAnalysis {
  id: string;
  document_count: number;
  conflict_count: number;
  findings: ConflictFinding[];
  notes: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  documents_indexed: number;
  model_provider: string;
  generation_model: string;
  embedding_model: string;
  max_upload_size_mb: number;
  storage_backend: string;
  ocr_enabled: boolean;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function isAuthExpiredError(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    error.status === 401 &&
    error.detail.toLowerCase().includes("token has expired")
  );
}

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";
const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.startsWith("http")
    ? configuredApiBaseUrl
    : `https://${configuredApiBaseUrl}`
  : window.location.port === "5173"
    ? "http://localhost:8000"
    : "";

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const raw = await response.text();
    let detail = raw || "Request failed.";
    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      detail = parsed.detail || detail;
    } catch {
      // Keep the raw body when the response is not JSON.
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, fullName: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, full_name: fullName, password }),
    }),

  health: () => request<HealthStatus>("/health"),

  listDocuments: (token: string) => request<DocumentRecord[]>("/documents", {}, token),

  previewDocument: (documentId: string, token: string) =>
    request<DocumentPreview>(`/documents/${documentId}/preview`, {}, token),

  uploadDocument: (file: File, token: string) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentRecord>(
      "/documents/upload",
      {
        method: "POST",
        body: formData,
      },
      token,
    );
  },

  reindexDocument: (documentId: string, token: string) =>
    request<{ message: string; document: DocumentRecord }>(
      `/documents/${documentId}/reindex`,
      { method: "POST" },
      token,
    ),

  deleteDocument: (documentId: string, token: string) =>
    request<{ message: string; document_id: string }>(
      `/documents/${documentId}`,
      { method: "DELETE" },
      token,
    ),

  updateDocumentPermissions: (documentId: string, visibility: "private" | "public", token: string) =>
    request<DocumentRecord>(
      `/documents/${documentId}/permissions`,
      {
        method: "PATCH",
        body: JSON.stringify({ visibility }),
      },
      token,
    ),

  query: (question: string, token: string) =>
    request<QueryResponse>(
      "/query",
      {
        method: "POST",
        body: JSON.stringify({ question }),
      },
      token,
    ),

  listLogs: (token: string) => request<AuditLogEntry[]>("/logs", {}, token),

  runEvaluation: (token: string) =>
    request<EvaluationRun>("/evaluations/run", { method: "POST" }, token),

  listEvaluations: (token: string) => request<EvaluationRun[]>("/evaluations", {}, token),

  listDocumentVersions: (documentId: string, token: string) =>
    request<DocumentRecord[]>(`/documents/${documentId}/versions`, {}, token),

  compareDocumentVersions: (baseDocumentId: string, targetDocumentId: string, token: string) =>
    request<VersionComparison>(
      `/documents/${baseDocumentId}/compare/${targetDocumentId}`,
      { method: "POST" },
      token,
    ),

  analyzeConflicts: (token: string) =>
    request<ConflictAnalysis>("/analysis/conflicts", { method: "POST" }, token),
};
