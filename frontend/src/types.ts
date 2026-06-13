// 前后端数据契约


// registry 里的文档记录
export type DocumentRecord = {
  document_id: string;
  original_filename?: string;
  stored_path?: string;
  file_type?: string;
  status?: string;
  chunk_count?: number;
  created_at?: string;
  updated_at?: string;
  error_message?: string;
  content_hash?: string;
  source_group_id?: string;
};

// 上传成功后返回
export type UploadResponse = {
  document_id: string;
  original_filename: string;
  stored_path: string;
  file_type: string;
  status: string;
  content_hash?: string;
  message?: string;
};

// RAG sources 类型
export type SourceItem = {
  document_id?: string;
  source?: string;
  file_type?: string;
  page?: number | string | null;
  section_title?: string | null;
  header_path?: string | null;
  chunk_index?: number | string | null;
};

export type ChatMode = "basic" | "agentic";

// 对应 /chat 请求体
export type ChatRequest = {
  question: string;
  document_id: string | null;
  top_k: number | null;
};

// 对应 /chat 返回体
export type ChatResponse = {
  question: string;
  answer: string;
  sources: SourceItem[];
};

export type AgentChatRequest = {
  question: string;
  document_id: string | null;
  top_k: number | null;
};

export type AgentChatResponse = {
  question: string;
  rewritten_query: string;
  answer: string;
  sources: SourceItem[];
  evidence_status: string;
  evidence_reason: string;
  grounding_status: string;
  grounding_reason: string;
  document_id: string | null;
  top_k: number;
};

// 对应 POST /documents/{document_id}/index
export type IndexResponse = {
  document_id: string;
  chunk_count: number;
  status: string;
  message?: string;
  deleted_old_chunks?: number;
};

// 对应 DELETE /documents/{document_id}
export interface DeleteDocumentResponse {
  document_id: string;
  deleted_chunks: number;
  registry_deleted: boolean;
  file_deleted: boolean;
  message: string;
}

// 前端本地聊天历史
export interface ChatHistoryItem {
  id: string;
  question: string;
  answer: string;
  sources: SourceItem[];
  document_id?: string | null;
  document_name?: string | null;
  createdAt: string;
  mode?: ChatMode;
  rewritten_query?: string;
  evidence_status?: string;
  evidence_reason?: string;
  grounding_status?: string;
  grounding_reason?: string;
}
