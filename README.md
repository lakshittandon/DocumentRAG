# Reliable RAG Document Intelligence Platform

This repository contains a full-stack final year project for a reliable Retrieval-Augmented Generation (RAG) document intelligence system with:

- FastAPI backend
- React + TypeScript frontend
- Hybrid retrieval with dense scoring, BM25, RRF, and reranking
- Citation-aware answer generation and sentence-level verification
- Document version metadata and previous-version comparison
- Multi-document conflict analysis for policy-style documents
- Prompt-injection guardrails and RAG-specific audit metadata
- Evaluation dashboard for retrieval, citation, refusal, hallucination, and latency signals
- PostgreSQL-backed document/chunk/audit persistence when `DATABASE_URL` is configured
- PostgreSQL-backed original-file storage with disk cache restoration for reindexing
- OCR fallback for scanned PDFs when Tesseract is available
- Docker/Render deployment from one public service
- Gemini-powered generation and embeddings through the Gemini API free tier

## Repository Layout

- `backend/` FastAPI application and core RAG pipeline
- `frontend/` React application for corpus, query, analysis, evaluation, and logs
- `deliverables/sample_documents/` sample PDF/Markdown document for testing the demo
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

Copy `.env.example` to `.env` at the repo root and set `GEMINI_API_KEY` before starting the backend if you want the real Gemini integration. Set `MODEL_PROVIDER=local` to stay on the offline fallback adapters.
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

## Default Demo Credentials

- Username: `admin`
- Password: `admin123`

## What Is Already Implemented

- Document upload, async ingestion, chunking, indexing, query, logging, evaluation, version comparison, and conflict-analysis routes
- Provider-agnostic model interfaces with Gemini adapters and deterministic local fallback adapters
- React demo screens for corpus management, querying, analysis, evaluation, and logs
- Sample document and Gemini-ready configuration for immediate local testing
- Project-plan source document and export script for `.docx`

## What You Can Extend Next

- Add migration tooling for production PostgreSQL schema changes
- Improve OCR quality controls and language packs for scanned PDFs
- Add richer admin analytics and full role policy management
- Add batch embeddings and persistent vector storage for larger corpora
