# Reliable RAG Document Intelligence Platform

This repository contains a full-stack final year project for a reliable Retrieval-Augmented Generation (RAG) document intelligence system with:

- FastAPI backend
- React + TypeScript frontend
- Hybrid retrieval with dense scoring, BM25, RRF, and reranking
- Citation-aware answer generation and sentence-level verification
- Document preview/source inspection with extracted text and chunk metadata
- Document version metadata and previous-version comparison
- Multi-document conflict analysis for policy-style documents
- Prompt-injection guardrails and RAG-specific audit metadata
- Evaluation dashboard for Recall@5, nDCG@5, MRR, citation, refusal, hallucination, and latency signals
- PostgreSQL-backed document/chunk/audit persistence when `DATABASE_URL` is configured
- PostgreSQL-backed original-file storage with disk cache restoration for reindexing
- OCR fallback for scanned PDFs when Tesseract is available
- Docker/Render deployment from one public service
- Gemini-powered generation and embeddings through the Gemini API free tier
- Query-time answer model toggle between Gemini hosted generation and Ollama/Qwen generation

## Repository Layout

- `backend/` FastAPI application and core RAG pipeline
- `frontend/` React application for corpus, query, analysis, evaluation, and logs
- `deliverables/` optional project artifacts and sample files generated during report preparation
- `docs/` project documentation, architecture notes, and deliverables
- `deployment/` Dockerfiles and deployment assets
- `scripts/` helper utilities such as project-plan docx export

## Quick Start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` at the repo root and set `GEMINI_API_KEY` before starting the backend if you want the real Gemini integration. The hosted Gemini default is `gemini-2.5-flash-lite`. Set `MODEL_PROVIDER=local` to stay on the deterministic offline fallback adapters. The Query Studio screen can switch answer generation between Gemini and Ollama/Qwen per question when both providers are configured.

For local Ollama, use `OLLAMA_BASE_URL=http://localhost:11434` and leave `OLLAMA_API_KEY` empty. For Ollama Cloud, use `OLLAMA_BASE_URL=https://ollama.com` and set `OLLAMA_API_KEY` to an API key from your Ollama account.
The default upload limit is `10 MB` to avoid long synchronous indexing delays on very large PDFs.
Set `DATABASE_URL` to use PostgreSQL persistence for documents, chunks, audit logs, and original uploaded files; otherwise the app falls back to in-memory stores.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Project Plan Docx

```bash
./scripts/export_project_plan.sh
```

The exported file is written to `docs/Reliable_RAG_Project_Plan.docx`.

## Public Deployment

For a single public resume/demo URL, deploy the repository on Render using [render.yaml](/Users/lakshittandon/Desktop/DocumentRAG/render.yaml).

The deployment image:

- builds the React frontend during the Docker build
- serves the frontend from the FastAPI app
- exposes the backend and UI from one public URL
- stores documents, chunks, audit logs, and uploaded file bytes in Render PostgreSQL when `DATABASE_URL` is present
- uses `/app/data/uploads` as an ephemeral working cache that can be restored from PostgreSQL for reindexing
- keeps the user corpus empty by default
- can run hosted Gemini by default and expose a Query Studio toggle for hosted Qwen through Ollama Cloud with `OLLAMA_BASE_URL=https://ollama.com`, `OLLAMA_MODEL=qwen2.5:0.5b`, and `OLLAMA_API_KEY`

## Login And Registration

The hosted demo opens on a real login/register screen. New users can create their own account, while the built-in demo account remains available from the `Use Demo Account` button for quick evaluation.

- Demo admin username: `admin`
- Demo admin password: `admin123`

## What Is Already Implemented

- Document upload, async ingestion, chunking, indexing, query, logging, evaluation, version comparison, and conflict-analysis routes
- Provider-agnostic model interfaces with Gemini adapters, a real Ollama chat adapter, deterministic local fallback adapters, and a per-query frontend model selector
- React demo screens for corpus management, source inspection, querying, analysis, evaluation, and logs
- Empty hosted corpus by default, plus Gemini-ready configuration for immediate local testing
- Project-plan source document and export script for `.docx`

## What You Can Extend Next

- Add migration tooling for production PostgreSQL schema changes
- Improve OCR quality controls and language packs for scanned PDFs
- Add a local embedding model for fully local Ollama retrieval in addition to local Ollama generation
- Add richer admin analytics and full role policy management
- Add batch embeddings and persistent vector storage for larger corpora
