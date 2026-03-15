import { useState, type ChangeEvent } from "react";

import type { DocumentRecord, HealthStatus } from "../lib/api";

interface DashboardPageProps {
  documents: DocumentRecord[];
  health: HealthStatus | null;
  onUpload: (file: File) => Promise<void>;
  onReindex: (documentId: string) => Promise<void>;
  onDelete: (document: DocumentRecord) => Promise<void>;
}

export function DashboardPage({ documents, health, onUpload, onReindex, onDelete }: DashboardPageProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

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
            <strong>{health?.benchmark_ready ? "Ready" : "Missing"}</strong>
            <span>Benchmark Status</span>
          </article>
          <article className="stat-pill">
            <strong>{health?.version ?? "0.1.0"}</strong>
            <span>Backend Version</span>
          </article>
          <article className="stat-pill">
            <strong>{health?.model_provider ?? "local"}</strong>
            <span>Model Provider</span>
          </article>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Upload a document</h3>
          <span className="panel-tag">{isUploading ? "Uploading" : "Ready"}</span>
        </div>

        <p className="muted">
          Maximum upload size: {health?.max_upload_size_mb ?? 10} MB. Large PDFs should be split before upload.
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
                    {document.page_count} pages • {document.chunk_count} chunks
                  </p>
                </div>
                <span className="status-chip">{document.status}</span>
              </div>

              <p className="muted">Checksum: {document.checksum.slice(0, 12)}...</p>
              <p className="muted">Updated: {new Date(document.updated_at).toLocaleString()}</p>

              <button
                type="button"
                className="secondary-button"
                onClick={() => onReindex(document.id)}
              >
                Reindex
              </button>
              <button
                type="button"
                className="secondary-button danger-button"
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
    </div>
  );
}
