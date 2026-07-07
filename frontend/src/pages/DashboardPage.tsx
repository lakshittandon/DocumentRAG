import { useState, type ChangeEvent } from "react";

import type { DocumentPreview, DocumentRecord, HealthStatus, VersionComparison } from "../lib/api";

interface DashboardPageProps {
  documents: DocumentRecord[];
  health: HealthStatus | null;
  onUpload: (file: File) => Promise<void>;
  onReindex: (documentId: string) => Promise<void>;
  onDelete: (document: DocumentRecord) => Promise<void>;
  onUpdateVisibility: (document: DocumentRecord, visibility: "private" | "public") => Promise<void>;
  onPreviewDocument: (document: DocumentRecord) => Promise<void>;
  onComparePreviousVersion: (document: DocumentRecord) => Promise<void>;
  versionComparison: VersionComparison | null;
  documentPreview: DocumentPreview | null;
}

export function DashboardPage({
  documents,
  health,
  onUpload,
  onReindex,
  onDelete,
  onUpdateVisibility,
  onPreviewDocument,
  onComparePreviousVersion,
  versionComparison,
  documentPreview,
}: DashboardPageProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [previewingDocumentId, setPreviewingDocumentId] = useState("");
  const [error, setError] = useState("");
  const ocrStatus = health
    ? health.ocr_enabled
      ? "enabled for scanned PDFs"
      : "not available in this environment"
    : "checking backend support";

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setIsUploading(true);
    setError("");
    try {
      await onUpload(file);
      event.target.value = "";
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Corpus Dashboard</p>
          <h2>Control the indexed knowledge base</h2>
          <p>
            Upload reproducible PDFs or text files, review indexing state, and reindex any document after changing chunking or retrieval logic.
          </p>
        </div>
        <div className="stats-strip">
          <article className="stat-pill">
            <strong>{health?.documents_indexed ?? documents.length}</strong>
            <span>Documents Indexed</span>
          </article>
          <article className="stat-pill">
            <strong>{health?.max_upload_size_mb ?? 10} MB</strong>
            <span>Upload Limit</span>
          </article>
          <article className="stat-pill">
            <strong>{health?.version ?? "0.1.0"}</strong>
            <span>Backend Version</span>
          </article>
          <article className="stat-pill">
            <strong>{health?.storage_backend ?? "memory"}</strong>
            <span>Storage Backend</span>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Upload a document</h3>
          <span className="panel-tag">{isUploading ? "Uploading" : "Ready"}</span>
        </div>

        <p className="muted">
          Maximum upload size: {health?.max_upload_size_mb ?? 10} MB. OCR is{" "}
          {ocrStatus}.
        </p>

        <label className="upload-zone">
          <input type="file" accept=".txt,.md,.pdf" onChange={handleFileChange} />
          <span>Choose a `.txt`, `.md`, or `.pdf` file</span>
        </label>

        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Indexed Documents</h3>
          <span className="panel-tag">{documents.length} total</span>
        </div>

        <div className="document-grid">
          {documents.map((document) => (
            <article key={document.id} className="document-card">
              <div className="document-card-top">
                <div>
                  <h4>{document.filename}</h4>
                  <p className="muted">
                    {document.status === "processing"
                      ? "Indexing in background..."
                      : `${document.page_count} pages • ${document.chunk_count} chunks`}
                  </p>
                  <p className="muted">
                    {(document.logical_name ?? document.filename)} · v{document.version}
                  </p>
                  <p className="muted">
                    Owner: {document.owner_username} · {document.visibility}
                  </p>
                </div>
                <span className="status-chip">{document.status}</span>
              </div>

              <p className="muted">Checksum: {document.checksum.slice(0, 12)}...</p>
              <p className="muted">Updated: {new Date(document.updated_at).toLocaleString()}</p>
              {document.error_message ? <p className="error-text">{document.error_message}</p> : null}

              <button
                type="button"
                className="secondary-button"
                disabled={document.status === "processing"}
                onClick={() => onReindex(document.id)}
              >
                Reindex
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={document.status !== "indexed" || previewingDocumentId === document.id}
                onClick={() => {
                  setPreviewingDocumentId(document.id);
                  void onPreviewDocument(document)
                    .catch((caughtError) => {
                      setError(
                        caughtError instanceof Error ? caughtError.message : "Document preview failed.",
                      );
                    })
                    .finally(() => setPreviewingDocumentId(""));
                }}
              >
                {previewingDocumentId === document.id ? "Inspecting..." : "Inspect Source"}
              </button>
              {document.previous_version_id ? (
                <button
                  type="button"
                  className="secondary-button"
                  disabled={document.status === "processing"}
                  onClick={() => {
                    void onComparePreviousVersion(document).catch((caughtError) => {
                      setError(
                        caughtError instanceof Error ? caughtError.message : "Version comparison failed.",
                      );
                    });
                  }}
                >
                  Compare Previous
                </button>
              ) : null}
              <button
                type="button"
                className="secondary-button"
                disabled={document.status === "processing"}
                onClick={() => {
                  const nextVisibility = document.visibility === "public" ? "private" : "public";
                  void onUpdateVisibility(document, nextVisibility).catch((caughtError) => {
                    setError(
                      caughtError instanceof Error ? caughtError.message : "Permission update failed.",
                    );
                  });
                }}
              >
                {document.visibility === "public" ? "Make Private" : "Make Public"}
              </button>
              <button
                type="button"
                className="secondary-button danger-button"
                disabled={document.status === "processing"}
                onClick={() => {
                  const confirmed = window.confirm(
                    `Delete ${document.filename} from the corpus? This removes the file from local storage too.`,
                  );
                  if (confirmed) {
                    void onDelete(document).catch((caughtError) => {
                      setError(
                        caughtError instanceof Error ? caughtError.message : "Delete failed.",
                      );
                    });
                  }
                }}
              >
                Delete
              </button>
            </article>
          ))}
        </div>
      </section>

      {documentPreview ? (
        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>Document Preview and Metadata</h3>
              <p className="muted">
                Source inspection for {documentPreview.document.filename} with extracted text, page sections, and chunk metadata.
              </p>
            </div>
            <span className="panel-tag">{documentPreview.chunks.length} shown chunks</span>
          </div>

          <div className="metadata-grid preview-metadata">
            <span>Content type: {documentPreview.document.content_type}</span>
            <span>Pages: {documentPreview.document.page_count}</span>
            <span>Indexed chunks: {documentPreview.document.chunk_count}</span>
            <span>Approx. tokens: {documentPreview.total_tokens}</span>
            <span>Checksum: {documentPreview.document.checksum}</span>
            <span>Visibility: {documentPreview.document.visibility}</span>
          </div>

          <div className="source-preview-box">
            <pre>{documentPreview.extracted_text || "No extracted text is available yet."}</pre>
          </div>

          <div className="chunk-preview-grid">
            {documentPreview.chunks.map((chunk) => (
              <article key={chunk.id} className="chunk-preview-card">
                <div className="panel-header">
                  <strong>Page {chunk.page}</strong>
                  <span className="panel-tag">{chunk.token_count} tokens</span>
                </div>
                <p className="muted">{chunk.section}</p>
                <p>{chunk.text}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {versionComparison ? (
        <section className="panel">
          <div className="panel-header">
            <h3>Version Comparison</h3>
            <span className="panel-tag">
              v{versionComparison.base_document.version} to v{versionComparison.target_document.version}
            </span>
          </div>
          <p className="muted">{versionComparison.summary}</p>

          <div className="comparison-grid">
            <article>
              <h4>Added Statements</h4>
              <div className="stack">
                {versionComparison.added.length === 0 ? (
                  <p className="muted">No added statements detected.</p>
                ) : (
                  versionComparison.added.map((change) => (
                    <div key={`${change.document_id}-${change.page}-${change.text}`} className="change-card added">
                      <p>{change.text}</p>
                      <small>
                        {change.document_name} v{change.version}, page {change.page}, {change.section}
                      </small>
                    </div>
                  ))
                )}
              </div>
            </article>

            <article>
              <h4>Removed Statements</h4>
              <div className="stack">
                {versionComparison.removed.length === 0 ? (
                  <p className="muted">No removed statements detected.</p>
                ) : (
                  versionComparison.removed.map((change) => (
                    <div key={`${change.document_id}-${change.page}-${change.text}`} className="change-card removed">
                      <p>{change.text}</p>
                      <small>
                        {change.document_name} v{change.version}, page {change.page}, {change.section}
                      </small>
                    </div>
                  ))
                )}
              </div>
            </article>
          </div>
        </section>
      ) : null}
    </div>
  );
}
