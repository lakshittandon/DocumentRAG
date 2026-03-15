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
  error_message?: string | null;
  created_at: string;
  updated_at: string;
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

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  support_score: number;
  unsupported_sentences: string[];
  retrieval_trace: QueryTrace;
}

export interface EvaluationRun {
  id: string;
  created_at: string;
  sample_count: number;
  retrieval_recall_at_5: number;
  mrr: number;
  ndcg_at_5: number;
  answer_accuracy: number;
  citation_accuracy: number;
  refusal_accuracy: number;
  hallucination_rate: number;
  notes: string;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  detail: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  documents_indexed: number;
  benchmark_ready: boolean;
  model_provider: string;
  generation_model: string;
  embedding_model: string;
  max_upload_size_mb: number;
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
    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      throw new Error(parsed.detail || "Request failed.");
    } catch {
      throw new Error(raw || "Request failed.");
    }
  }

  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  health: () => request<HealthStatus>("/health"),

  listDocuments: (token: string) => request<DocumentRecord[]>("/documents", {}, token),

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

  query: (question: string, token: string) =>
    request<QueryResponse>(
      "/query",
      {
        method: "POST",
        body: JSON.stringify({ question }),
      },
      token,
    ),

  runEvaluation: (token: string) =>
    request<EvaluationRun>("/evaluations/run", { method: "POST" }, token),

  listEvaluations: (token: string) => request<EvaluationRun[]>("/evaluations", {}, token),

  listLogs: (token: string) => request<AuditLogEntry[]>("/logs", {}, token),
};
