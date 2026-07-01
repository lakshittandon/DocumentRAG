# Architecture Overview

## Backend Flow

1. A user logs in through `/auth/login` and receives a signed access token.
2. Documents are uploaded through `/documents/upload` and stored under `data/uploads/`.
3. The parser extracts page-level text and metadata from TXT, Markdown, and text-based PDF inputs, with simple PDF table extraction when available.
4. The chunker creates overlapping chunks tagged with document, page, and section metadata.
5. The retrieval engine runs dense retrieval and BM25 retrieval, fuses them with RRF, and reranks the result set.
6. The generator creates a grounded answer from the strongest evidence chunks.
7. The verifier scores answer support and flags unsupported sentences.
8. Version comparison can diff indexed versions of the same logical document.
9. Conflict analysis scans policy-style statements across documents for likely contradictions.
10. Evaluation runs call the same query path repeatedly against a fixed benchmark pack.

## Frontend Flow

1. The React app authenticates a user and stores the bearer token in local storage.
2. The corpus dashboard shows health status, current documents, upload controls, and reindex actions.
3. The query studio sends questions to the backend and renders answers, citations, and reranked evidence.
4. The analysis lab scans for likely cross-document conflicts.
5. The evaluation lab launches benchmark runs and summarizes retrieval and answer quality metrics.
6. The audit trail view exposes admin-visible system and user events.

## Extension Points

- The backend can run with Gemini-hosted generation and embeddings or with local fallback adapters depending on `MODEL_PROVIDER`.
- Replace in-memory stores with persistent PostgreSQL-backed repositories.
- Add OCR for scanned/image-only PDFs and stronger table extraction for complex PDF documents.
- Move retrieval indices to external Qdrant and Whoosh services as the corpus grows.
