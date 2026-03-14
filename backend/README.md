# Backend

The backend exposes a FastAPI service for authentication, document ingestion, query handling, benchmark evaluation, and audit logging.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Notes

- The current implementation supports `MODEL_PROVIDER=gemini` using the Gemini REST API and `MODEL_PROVIDER=local` as an offline fallback.
- Set `GEMINI_API_KEY` and keep `GEMINI_GENERATION_MODEL=gemini-2.5-flash-lite` plus `GEMINI_EMBEDDING_MODEL=gemini-embedding-001` to use the hosted Gemini path.
- The application still uses in-memory repositories; PostgreSQL and Qdrant are part of the target architecture but are not yet wired into persistence.
