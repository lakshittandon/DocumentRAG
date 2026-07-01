import { useState } from "react";

import type { ConflictAnalysis } from "../lib/api";

interface AnalysisPageProps {
  analysis: ConflictAnalysis | null;
  onAnalyzeConflicts: () => Promise<void>;
}

export function AnalysisPage({ analysis, onAnalyzeConflicts }: AnalysisPageProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");

  const handleRun = async () => {
    setIsRunning(true);
    setError("");
    try {
      await onAnalyzeConflicts();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Conflict analysis failed.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Analysis Lab</p>
          <h2>Detect possible conflicts across indexed documents</h2>
          <p>
            Scans policy-style statements across the corpus and flags likely contradictions with source
            document and page references.
          </p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Multi-document Conflict Detection</h3>
          <span className="panel-tag">{analysis?.conflict_count ?? 0} conflicts</span>
        </div>
        <p className="muted">
          Works best with documents that contain comparable policy values, dates, limits, approval roles,
          amounts, or numeric rules.
        </p>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="button" onClick={handleRun} disabled={isRunning}>
          {isRunning ? "Scanning corpus..." : "Run Conflict Scan"}
        </button>
      </section>

      {analysis ? (
        <section className="panel">
          <div className="panel-header">
            <h3>Conflict Findings</h3>
            <span className="panel-tag">{analysis.document_count} documents scanned</span>
          </div>
          <p className="muted">{analysis.notes}</p>

          <div className="conflict-list">
            {analysis.findings.length === 0 ? (
              <p className="muted">No likely conflicts detected in the current indexed corpus.</p>
            ) : (
              analysis.findings.map((finding) => (
                <article
                  key={`${finding.document_a_id}-${finding.document_b_id}-${finding.statement_a}`}
                  className="conflict-card"
                >
                  <div className="panel-header">
                    <h4>{finding.topic}</h4>
                    <span className="panel-tag">Possible conflict</span>
                  </div>
                  <div className="comparison-grid">
                    <div className="change-card removed">
                      <strong>{finding.document_a}</strong>
                      <p>{finding.statement_a}</p>
                      <small>Page {finding.page_a}</small>
                    </div>
                    <div className="change-card added">
                      <strong>{finding.document_b}</strong>
                      <p>{finding.statement_b}</p>
                      <small>Page {finding.page_b}</small>
                    </div>
                  </div>
                  <p className="muted">{finding.reason}</p>
                </article>
              ))
            )}
          </div>
        </section>
      ) : null}
    </div>
  );
}
