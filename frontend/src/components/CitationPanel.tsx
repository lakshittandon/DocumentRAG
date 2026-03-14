import type { Citation, RetrievalHit } from "../lib/api";

interface CitationPanelProps {
  citations: Citation[];
  rerankedHits: RetrievalHit[];
}

export function CitationPanel({ citations, rerankedHits }: CitationPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>Evidence and Citations</h3>
        <span className="panel-tag">{citations.length} citations</span>
      </div>

      <div className="stack">
        {citations.length === 0 ? (
          <p className="muted">
            No citations were attached because the pipeline returned a refusal or no evidence cleared the threshold.
          </p>
        ) : (
          citations.map((citation) => (
            <article key={citation.chunk_id} className="source-card">
              <div className="source-head">
                <strong>{citation.document_name}</strong>
                <span>
                  Page {citation.page} / {citation.section}
                </span>
              </div>
              <p>{citation.snippet}</p>
              <small>Score: {citation.score.toFixed(3)}</small>
            </article>
          ))
        )}
      </div>

      {rerankedHits.length > 0 && (
        <>
          <div className="panel-header">
            <h3>Reranked Retrieval Trace</h3>
            <span className="panel-tag">{rerankedHits.length} hits</span>
          </div>
          <div className="trace-grid">
            {rerankedHits.map((hit) => (
              <article key={`${hit.source}-${hit.chunk_id}`} className="trace-card">
                <div className="trace-title">
                  <strong>{hit.document_name}</strong>
                  <span>{hit.score.toFixed(3)}</span>
                </div>
                <p>{hit.text.slice(0, 180)}...</p>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

