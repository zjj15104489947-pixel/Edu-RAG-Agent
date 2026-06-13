// 前后端连接层

import type {
  AgentChatRequest,
  AgentChatResponse,
  ChatRequest,
  ChatResponse,
  DeleteDocumentResponse,
  DocumentRecord,
  IndexResponse,
  UploadResponse,
} from "./types";

const API_BASE = "/api";

// 把后端错误转成便于查看的文字
async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return data.detail;
    }
    return JSON.stringify(data);
  } catch {
    return response.statusText || "Request failed";
  }
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<T>;
}

// GET /api/health
export async function checkHealth(): Promise<boolean> {
  try {
    const result = await requestJson<{ status?: string }>("/health");
    return result.status === "ok";
  } catch {
    return false;
  }
}

// GET /api/documents
export async function listDocuments(): Promise<DocumentRecord[]> {
  const result = await requestJson<{ documents: DocumentRecord[] }>("/documents");
  return result.documents;
}

// POST /api/documents/upload
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return requestJson<UploadResponse>("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

// POST /api/documents/{document_id}/index
export async function indexDocument(documentId: string): Promise<IndexResponse> {
  return requestJson<IndexResponse>(`/documents/${encodeURIComponent(documentId)}/index`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chunk_size: null,
      chunk_overlap: null,
    }),
  });
}

// DELETE /api/documents/{document_id}
export async function deleteDocument(documentId: string): Promise<DeleteDocumentResponse> {
  return requestJson<DeleteDocumentResponse>(
    `/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
    }
  );
}

// POST /api/chat
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

// POST /api/agent/chat
export async function agentChat(request: AgentChatRequest): Promise<AgentChatResponse> {
  return requestJson<AgentChatResponse>("/agent/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}
