# Edu-RAG-Agent Frontend

This is the Vite + React + TypeScript frontend for Edu-RAG-Agent.

## Start Backend First

```powershell
uvicorn backend.main:app --reload
```

Backend address:

```text
http://127.0.0.1:8000
```

## Install Dependencies

```powershell
cd frontend
npm install
```

## Start Frontend

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## API Proxy

The frontend calls backend APIs through `/api`:

```text
/api/health
/api/documents
/api/documents/upload
/api/documents/{document_id}/index
/api/documents/{document_id}
/api/chat
/api/agent/chat
```

Vite proxies `/api` to:

```text
http://127.0.0.1:8000
```

and removes the `/api` prefix before forwarding.

## Demo Features

The frontend supports:

- Backend online/offline status.
- Uploading PDF / Markdown files.
- Listing document registry records.
- Selecting one document for scoped chat.
- Clear selection for searching across all indexed documents.
- Index and Re-index actions.
- Delete document with browser confirmation.
- Single-turn RAG chat through the backend.
- Basic RAG mode through `/api/chat`.
- Agentic RAG mode through `/api/agent/chat`.
- Agentic RAG result display for rewritten query, evidence check, and grounding check.
- Local chat history and Clear chat.
- Latest answer and sources display.
