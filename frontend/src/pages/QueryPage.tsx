import { useState, type FormEvent } from "react";

import { CitationPanel } from "../components/CitationPanel";
import type { QueryResponse } from "../lib/api";

interface QueryPageProps {
  result: QueryResponse | null;
  onSubmitQuestion: (question: string) => Promise<void>;
}

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
              <span className="panel-tag">Support {result.support_score.toFixed(3)}</span>
            </div>
            <p className="answer-text">{result.answer}</p>

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

          <CitationPanel
            citations={result.citations}
            rerankedHits={result.retrieval_trace.reranked_hits}
          />
        </>
      ) : null}
    </div>
  );
}
