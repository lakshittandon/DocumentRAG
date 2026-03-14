# Reliable RAG Document Intelligence Platform

This repository contains a full-stack final year project scaffold for a reliable Retrieval-Augmented Generation (RAG) system with:

- FastAPI backend
- React + TypeScript frontend
- Hybrid retrieval with dense scoring, BM25, RRF, and reranking
- Citation-aware answer generation and sentence-level verification
- Evaluation harness with retrieval and answer quality metrics
- Docker-based local deployment topology with PostgreSQL and Qdrant
- Gemini-powered generation and embeddings through the Gemini API free tier

## Repository Layout

- `backend/` FastAPI application and core RAG pipeline
- `frontend/` React application for login, corpus, query, evaluation, and logs
- `data/corpus/` reproducible demo corpus used for first-run seeding
- `data/evaluations/` benchmark inputs for automated evaluation runs
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

## Default Demo Credentials

- Username: `admin`
- Password: `admin123`

## What Is Already Implemented

- Document upload, ingestion, chunking, indexing, query, logging, and evaluation routes
- Provider-agnostic model interfaces with Gemini adapters and deterministic local fallback adapters
- React demo screens for login, corpus management, querying, evaluations, and logs
- Demo corpus and benchmark data for immediate local testing
- Project-plan source document and export script for `.docx`

## What You Can Extend Next

- Replace in-memory repositories with persistent PostgreSQL-backed repositories
- Add OCR for scanned PDFs
- Add richer admin analytics and role policy enforcement
- Add batch embeddings and persistent vector storage for larger corpora
