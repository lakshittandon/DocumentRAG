import { useState } from "react";

import type { EvaluationRun } from "../lib/api";

interface EvaluationPageProps {
  runs: EvaluationRun[];
  onRunEvaluation: () => Promise<void>;
}

const METRICS: Array<{ key: keyof EvaluationRun; label: string; format?: "percent" | "ms" | "number" }> = [
  { key: "recall_at_5", label: "Recall@5", format: "percent" },
  { key: "ndcg_at_5", label: "nDCG@5", format: "number" },
  { key: "mrr", label: "MRR", format: "number" },
  { key: "answer_accuracy", label: "Answer Accuracy", format: "percent" },
  { key: "citation_correctness", label: "Citation Correctness", format: "percent" },
  { key: "refusal_accuracy", label: "Refusal Accuracy", format: "percent" },
  { key: "hallucination_rate", label: "Hallucination Rate", format: "percent" },
  { key: "avg_latency_ms", label: "Avg Latency", format: "ms" },
];

function formatMetric(value: unknown, format: "percent" | "ms" | "number" = "number") {
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return "-";
  }
  if (format === "percent") {
    return `${(numberValue * 100).toFixed(0)}%`;
  }
  if (format === "ms") {
    return `${numberValue.toFixed(0)} ms`;
  }
  return numberValue.toFixed(3);
}

export function EvaluationPage({ runs, onRunEvaluation }: EvaluationPageProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const latestRun = runs[0];

  const handleRun = async () => {
    setIsRunning(true);
    setError("");
    try {
      await onRunEvaluation();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Evaluation failed.");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Evaluation Lab</p>
          <h2>Benchmark the current retrieval and answer pipeline</h2>
          <p>
            Runs a fixed demo benchmark subset against the currently uploaded corpus and reports retrieval,
            citation, refusal, latency, and hallucination signals without exhausting hosted model limits.
          </p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Run Benchmark</h3>
          <span className="panel-tag">{runs.length} runs</span>
        </div>
        <p className="muted">
          Hosted runs use a smaller default sample set for Gemini rate limits. For deeper report runs,
          call the API with a larger sample_limit locally or after increasing provider quota.
        </p>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="button" onClick={handleRun} disabled={isRunning}>
          {isRunning ? "Running benchmark..." : "Run Benchmark"}
        </button>
      </section>

      {latestRun ? (
        <>
          <section className="panel">
            <div className="panel-header">
              <h3>Latest Results</h3>
              <span className="panel-tag">{latestRun.sample_count} samples</span>
            </div>
            <div className="metrics-grid">
              {METRICS.map((metric) => (
                <article key={metric.key} className="metric-card">
                  <strong>{formatMetric(latestRun[metric.key], metric.format)}</strong>
                  <span>{metric.label}</span>
                </article>
              ))}
            </div>
            <p className="muted">{latestRun.notes}</p>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h3>Sample Results</h3>
              <span className="panel-tag">{latestRun.estimated_model_calls} model calls</span>
            </div>
            <div className="sample-list">
              {latestRun.samples.map((sample) => (
                <article key={sample.question} className={sample.passed ? "sample-card passed" : "sample-card failed"}>
                  <div className="sample-head">
                    <strong>{sample.passed ? "Passed" : "Needs review"}</strong>
                    <span>{sample.category} · {sample.latency_ms.toFixed(0)} ms</span>
                  </div>
                  <p>{sample.question}</p>
                  <small>
                    Recall@5 {sample.recall_at_5.toFixed(1)} / nDCG@5 {sample.ndcg_at_5.toFixed(3)} / MRR {sample.reciprocal_rank.toFixed(3)} /
                    Citation {sample.citation_correct ? "correct" : "missing"} /
                    {sample.refused ? " refused" : " answered"}
                  </small>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
