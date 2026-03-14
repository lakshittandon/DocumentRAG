import { useState } from "react";

import type { EvaluationRun } from "../lib/api";

interface EvaluationsPageProps {
  runs: EvaluationRun[];
  onRunEvaluation: () => Promise<void>;
}

export function EvaluationsPage({ runs, onRunEvaluation }: EvaluationsPageProps) {
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = async () => {
    setError("");
    setIsRunning(true);
    try {
      await onRunEvaluation();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Evaluation failed.");
    } finally {
      setIsRunning(false);
    }
  };

  const latest = runs[0];

  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Evaluation Lab</p>
          <h2>Benchmark retrieval and answer faithfulness</h2>
          <p>
            Run the seeded benchmark to capture Recall@5, MRR, nDCG@5, answer accuracy, citation accuracy, refusal accuracy, and hallucination rate.
          </p>
        </div>
        <button type="button" className="primary-button" onClick={handleRun} disabled={isRunning}>
          {isRunning ? "Running evaluation..." : "Run Benchmark"}
        </button>
      </section>

      {error ? <p className="error-text">{error}</p> : null}

      {latest ? (
        <section className="metrics-grid">
          <article className="metric-card">
            <strong>{latest.retrieval_recall_at_5}</strong>
            <span>Recall@5</span>
          </article>
          <article className="metric-card">
            <strong>{latest.mrr}</strong>
            <span>MRR</span>
          </article>
          <article className="metric-card">
            <strong>{latest.ndcg_at_5}</strong>
            <span>nDCG@5</span>
          </article>
          <article className="metric-card">
            <strong>{latest.answer_accuracy}</strong>
            <span>Answer Accuracy</span>
          </article>
          <article className="metric-card">
            <strong>{latest.citation_accuracy}</strong>
            <span>Citation Accuracy</span>
          </article>
          <article className="metric-card">
            <strong>{latest.refusal_accuracy}</strong>
            <span>Refusal Accuracy</span>
          </article>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header">
          <h3>Evaluation History</h3>
          <span className="panel-tag">{runs.length} runs</span>
        </div>

        <div className="stack">
          {runs.map((run) => (
            <article key={run.id} className="run-card">
              <div className="run-card-head">
                <strong>{new Date(run.created_at).toLocaleString()}</strong>
                <span>{run.sample_count} samples</span>
              </div>
              <p className="muted">{run.notes}</p>
              <div className="run-metrics">
                <span>Recall@5: {run.retrieval_recall_at_5}</span>
                <span>MRR: {run.mrr}</span>
                <span>nDCG@5: {run.ndcg_at_5}</span>
                <span>Hallucination: {run.hallucination_rate}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

