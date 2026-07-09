# Backend

The backend exposes a FastAPI service for authentication, document ingestion, query handling, version comparison, conflict analysis, benchmark evaluation, and audit logging.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Notes

- The current implementation supports `MODEL_PROVIDER=gemini` using the Gemini REST API, `MODEL_PROVIDER=ollama` using an Ollama chat server, and `MODEL_PROVIDER=local` as a deterministic offline fallback.
- Set `GEMINI_API_KEY` and keep `GEMINI_GENERATION_MODEL=gemini-3.1-flash-lite` plus `GEMINI_EMBEDDING_MODEL=gemini-embedding-001` to use the hosted Gemini path.
- `/query` accepts `model_provider=gemini` or `model_provider=ollama`, so Query Studio can switch answer generation between Gemini and Ollama/Qwen without changing retrieval or redeploying.
- Document preview is available through `/documents/{document_id}/preview`, returning extracted text and chunk/page metadata for source inspection.
- Set `OLLAMA_BASE_URL=http://localhost:11434` and `OLLAMA_MODEL=qwen2.5:0.5b` to use the local Ollama path. For Ollama Cloud, set `OLLAMA_BASE_URL=https://ollama.com` and `OLLAMA_API_KEY`.
- The application uses PostgreSQL-backed document/chunk/audit/original-file persistence when `DATABASE_URL` is set; otherwise it falls back to in-memory repositories for local tests.
- Text PDFs and simple PDF tables are supported through `pdfplumber`; scanned/image-only PDFs use OCR when Tesseract is installed.
