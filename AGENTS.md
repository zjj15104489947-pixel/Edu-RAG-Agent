# AGENTS.md

## Project Positioning

`Edu-RAG-Agent` is a local v0 Agentic RAG prototype for course materials. It is intended for learning, local demos, and internship interviews. Do not describe it as production-ready, enterprise-grade, high-concurrency, or suitable for large-scale deployment.

## Architecture

```text
backend/     FastAPI entry point, schemas, and thin routes
core/        Settings and DeepSeek model creation
graphs/      Synchronous LangGraph Agentic RAG workflow
loaders/     PDF and Markdown reading
rag/         LangChain chunking, embeddings, Chroma, prompts
services/    Document lifecycle and QA business logic
scripts/     Local development and inspection commands
frontend/    Vite + React + TypeScript UI
```

## Current Flows

Document lifecycle:

```text
upload → registry → index/re-index → Chroma → delete
```

Basic RAG:

```text
POST /chat → retrieve → answer → sources
```

Agentic RAG:

```text
POST /agent/chat
→ rewrite_query
→ retrieve
→ check_evidence
→ generate_answer
→ check_grounding
```

The LangGraph workflow is synchronous and supplements `/chat`; it must not replace the baseline route without an explicit request.

## Development Rules

1. Prefer small, staged changes. Do not rewrite the whole project.
2. Keep FastAPI routes thin and business logic in `services/`.
3. Keep retrieval and model utilities in `rag/`, file reading in `loaders/`, and configuration in `core/config.py`.
4. Preserve document metadata and the uploaded `document_id` throughout indexing and retrieval.
5. Do not add LangGraph nodes unless they solve a concrete workflow problem.
6. Do not add MinerU / OCR directly to the main pipeline; use an optional adapter layer when requested.
7. Do not hardcode API keys, tokens, passwords, or local machine paths.
8. After code changes, state how to run and verify them.

## Repository Hygiene

Never commit:

- `.env` or real API keys
- `.venv/` or model caches
- `data/raw/uploads/`
- local course-material PDF/Markdown files under `data/raw/`
- SQLite registry files or Chroma persistence data
- `frontend/node_modules/` or `frontend/dist/`
- `__pycache__/`, `.pyc`, logs, editor-specific files

Only `.env.example` should contain configuration placeholders.

## Current API

```text
GET    /health
GET    /documents
GET    /documents/{document_id}
POST   /documents/upload
POST   /documents/{document_id}/index
DELETE /documents/{document_id}
POST   /chat
POST   /agent/chat
```

`POST /documents/index-local` exists for local development. Treat it as a local-only utility, not a public production endpoint.

## Known Limits

- Text PDFs and UTF-8 Markdown are the supported ingestion paths.
- Indexing and QA are synchronous.
- BGE-M3 is large and can be slow on CPU.
- SQLite and local Chroma target a single-machine demo.
- Frontend chat history is in-memory only.
- No authentication, authorization, task queue, streaming, OCR, or automated RAG evaluation is implemented.

## Verification

Backend checks:

```powershell
.venv\Scripts\python.exe -m compileall core loaders rag services graphs backend scripts
.venv\Scripts\python.exe -c "import backend.main; print('backend main import ok')"
.venv\Scripts\python.exe -c "from graphs.edu_qa_graph import build_edu_qa_graph; print(type(build_edu_qa_graph()).__name__)"
```

Frontend check:

```powershell
cd frontend
npm run build
```
