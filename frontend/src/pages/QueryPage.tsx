import { useState, type FormEvent } from "react";

import { CitationPanel } from "../components/CitationPanel";
import type { QueryResponse } from "../lib/api";

interface QueryPageProps {
  result: QueryResponse | null;
  onSubmitQuestion: (question: string) => Promise<void>;
}

const SUPPORT_LABELS: Record<string, string> = {
  supported: "Supported",
  partially_supported: "Partially supported",
  unsupported: "Unsupported",
};

export function QueryPage({ result, onSubmitQuestion }: QueryPageProps) {
  const [question, setQuestion] = useState("Which metrics are used to evaluate retrieval quality?");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await onSubmitQuestion(question);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Query failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="stack">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Query Studio</p>
          <h2>Ask grounded questions against the corpus</h2>
          <p>
            The backend runs dense retrieval, BM25 retrieval, RRF fusion, reranking, answer generation, and sentence-level verification before returning the response.
          </p>
        </div>
      </section>

      <section className="panel">
        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Question</span>
            <textarea
              rows={4}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isLoading}>
            {isLoading ? "Running pipeline..." : "Run Query"}
          </button>
        </form>
      </section>

      {result ? (
        <>
          <section className="panel">
            <div className="panel-header">
              <h3>Generated Answer</h3>
              <span className="panel-tag">Support {(result.support_score * 100).toFixed(0)}%</span>
            </div>
            <div className="trust-strip">
              <span className={result.refused ? "status-chip danger-chip" : "status-chip success-chip"}>
                {result.refused ? "Refused" : "Answered"}
              </span>
              {result.guarded ? <span className="status-chip danger-chip">Prompt guard</span> : null}
              <span className="status-chip">{result.latency_ms.toFixed(0)} ms</span>
              <span className="status-chip">{result.citations.length} citations</span>
            </div>
            <p className="answer-text">{result.answer}</p>

            {result.refusal_reason ? (
              <div className="warning-box">
                <strong>Refusal reason</strong>
                <p>{result.refusal_reason}</p>
              </div>
            ) : null}

            {result.unsupported_sentences.length > 0 && (
              <div className="warning-box">
                <strong>Unsupported sentences detected</strong>
                <ul>
                  {result.unsupported_sentences.map((sentence) => (
                    <li key={sentence}>{sentence}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {result.sentence_support.length > 0 ? (
            <section className="panel">
              <div className="panel-header">
                <h3>Claim Support Verification</h3>
                <span className="panel-tag">{result.sentence_support.length} sentences</span>
              </div>
              <div className="claim-list">
                {result.sentence_support.map((item, index) => (
                  <article key={`${item.status}-${index}`} className={`claim-card ${item.status}`}>
                    <div className="claim-card-head">
                      <strong>{SUPPORT_LABELS[item.status] ?? item.status}</strong>
                      <span>{item.best_overlap} overlap terms</span>
                    </div>
                    <p>{item.sentence}</p>
                    {item.reason ? <small>{item.reason}</small> : null}
                  </article>
                ))}
              </div>
            </section>
          ) : null}

          {result.retrieved_documents.length > 0 ? (
            <section className="panel">
              <div className="panel-header">
                <h3>Retrieved Documents</h3>
                <span className="panel-tag">{result.retrieved_documents.length} documents</span>
              </div>
              <div className="chip-row">
                {result.retrieved_documents.map((document) => (
                  <span key={document} className="status-chip">{document}</span>
                ))}
              </div>
            </section>
          ) : null}

          <CitationPanel
            citations={result.citations}
            rerankedHits={result.retrieval_trace.reranked_hits}
          />
        </>
      ) : null}
    </div>
  );
}
