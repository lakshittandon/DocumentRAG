# Architecture Overview

## Backend Flow

1. A user logs in through `/auth/login` and receives a signed access token.
2. Documents are uploaded through `/documents/upload` and stored under `data/uploads/`.
3. When PostgreSQL is configured, document metadata, chunks, audit logs, and original file bytes are persisted in the database; the upload directory acts as a working cache.
4. The parser extracts page-level text and metadata from TXT, Markdown, and PDFs, with simple PDF table extraction and OCR fallback for scanned pages when Tesseract is available.
5. The chunker creates overlapping chunks tagged with document, page, and section metadata.
6. The retrieval engine runs dense retrieval and BM25 retrieval, fuses them with RRF, and reranks the result set.
7. The generator creates a grounded answer from the strongest evidence chunks.
8. The verifier scores answer support and flags unsupported sentences.
9. Version comparison can diff indexed versions of the same logical document.
10. Conflict analysis scans policy-style statements across documents for likely contradictions.
11. Evaluation runs call the same query path repeatedly against a fixed benchmark pack.

## Frontend Flow

1. The React app authenticates a user and stores the bearer token in local storage.
2. The corpus dashboard shows health status, current documents, upload controls, and reindex actions.
3. The query studio sends questions to the backend and renders answers, citations, and reranked evidence.
4. The analysis lab scans for likely cross-document conflicts.
5. The evaluation lab launches benchmark runs and summarizes retrieval and answer quality metrics.
6. The audit trail view exposes admin-visible system and user events.

## Extension Points

- The backend can run with Gemini-hosted generation and embeddings or with local fallback adapters depending on `MODEL_PROVIDER`.
- Add stronger table extraction for complex PDF documents.
- Move retrieval indices to external Qdrant and Whoosh services as the corpus grows.
