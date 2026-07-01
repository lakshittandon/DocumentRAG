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

- Replace in-memory repositories with persistent PostgreSQL-backed repositories
- Add OCR for scanned PDFs; current PDF table extraction is text/table based through `pdfplumber`
- Add richer admin analytics and full role policy management
- Add batch embeddings and persistent vector storage for larger corpora
