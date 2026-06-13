import { useEffect, useMemo, useState } from "react";

import {
  agentChat,
  chat,
  checkHealth,
  deleteDocument,
  indexDocument,
  listDocuments,
  uploadDocument,
} from "./api";
import type {
  AgentChatResponse,
  ChatHistoryItem,
  ChatMode,
  DocumentRecord,
  SourceItem,
  UploadResponse,
} from "./types";

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  return String(value);
}

function sourceFields(source: SourceItem): Array<[string, string]> {
  const fields: Array<[string, string]> = [
    ["document_id", formatValue(source.document_id)],
    ["source", formatValue(source.source)],
    ["file_type", formatValue(source.file_type)],
    ["page", formatValue(source.page)],
    ["section_title", formatValue(source.section_title)],
    ["header_path", formatValue(source.header_path)],
    ["chunk_index", formatValue(source.chunk_index)],
  ];

  return fields.filter(([, value]) => value.length > 0);
}

function makeHistoryId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random()}`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function sourceSummary(source: SourceItem): string {
  const parts = [
    source.source,
    source.page ? `page ${source.page}` : "",
    source.section_title,
    source.header_path,
    source.chunk_index ? `chunk ${source.chunk_index}` : "",
  ].filter(Boolean);

  return parts.join(" | ") || "Source metadata";
}

function modeLabel(mode?: ChatMode): string {
  return mode === "agentic" ? "Agentic RAG" : "Basic RAG";
}

function statusClassName(status: string): string {
  const normalized = status.toUpperCase();
  if (normalized === "SUFFICIENT" || normalized === "GROUNDED") {
    return "success";
  }
  if (normalized === "INSUFFICIENT") {
    return "warning";
  }
  if (normalized === "UNGROUNDED") {
    return "danger";
  }
  return "neutral";
}

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [chatMode, setChatMode] = useState<ChatMode>("agentic");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const [rewrittenQuery, setRewrittenQuery] = useState("");
  const [evidenceStatus, setEvidenceStatus] = useState("");
  const [evidenceReason, setEvidenceReason] = useState("");
  const [groundingStatus, setGroundingStatus] = useState("");
  const [groundingReason, setGroundingReason] = useState("");
  const [error, setError] = useState("");
  const [backendOnline, setBackendOnline] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [indexingDocumentId, setIndexingDocumentId] = useState("");
  const [deletingDocumentId, setDeletingDocumentId] = useState("");
  const [answering, setAnswering] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === selectedDocumentId),
    [documents, selectedDocumentId]
  );

  const searchScopeLabel = selectedDocumentId
    ? "Selected document"
    : "All indexed documents";

  async function refreshDocuments() {
    setLoadingDocuments(true);
    try {
      const nextDocuments = await listDocuments();
      setDocuments(nextDocuments);
      setSelectedDocumentId((currentId) => {
        if (!currentId) {
          return null;
        }
        return nextDocuments.some((doc) => doc.document_id === currentId)
          ? currentId
          : null;
      });
      setError("");
    } catch (exc) {
      setError(`文档列表刷新失败: ${(exc as Error).message}`);
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function refreshBackendStatus() {
    const online = await checkHealth();
    setBackendOnline(online);
    if (!online) {
      setError("后端未启动或无法连接，请先启动 uvicorn backend.main:app --reload。");
    }
  }

  useEffect(() => {
    refreshBackendStatus();
    refreshDocuments();
  }, []);

  async function handleUpload() {
    if (!selectedFile) {
      setError("未选择文件。");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const result = await uploadDocument(selectedFile);
      setUploadResult(result);
      setSelectedDocumentId(result.document_id);
      await refreshDocuments();
    } catch (exc) {
      setError(`上传失败: ${(exc as Error).message}`);
    } finally {
      setUploading(false);
    }
  }

  async function handleIndex(documentId: string) {
    setIndexingDocumentId(documentId);
    setError("");

    try {
      await indexDocument(documentId);
      await refreshDocuments();
    } catch (exc) {
      setError(`索引失败: ${(exc as Error).message}`);
    } finally {
      setIndexingDocumentId("");
    }
  }

  async function handleDelete(doc: DocumentRecord) {
    const confirmed = window.confirm(
      `Delete document "${doc.original_filename || doc.document_id}"?\n\nThis will remove its registry record, vector chunks, and uploaded file if applicable.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(doc.document_id);
    setError("");

    try {
      await deleteDocument(doc.document_id);
      if (selectedDocumentId === doc.document_id) {
        setSelectedDocumentId(null);
      }
      if (uploadResult?.document_id === doc.document_id) {
        setUploadResult(null);
      }
      await refreshDocuments();
    } catch (exc) {
      setError(`删除失败: ${(exc as Error).message}`);
    } finally {
      setDeletingDocumentId("");
    }
  }

  async function handleAsk() {
    if (!question.trim()) {
      setError("问题不能为空。");
      return;
    }

    const currentQuestion = question.trim();
    const requestDocumentId = selectedDocumentId || null;
    const documentName =
      selectedDocument?.original_filename || "All indexed documents";

    setAnswering(true);
    setError("");
    setAnswer("");
    setSources([]);
    setRewrittenQuery("");
    setEvidenceStatus("");
    setEvidenceReason("");
    setGroundingStatus("");
    setGroundingReason("");

    try {
      const payload = {
        question: currentQuestion,
        document_id: requestDocumentId,
        top_k: topK,
      };

      if (chatMode === "agentic") {
        const result: AgentChatResponse = await agentChat(payload);
        const nextSources = result.sources ?? [];
        const nextAnswer = result.answer;

        setAnswer(nextAnswer);
        setSources(nextSources);
        setRewrittenQuery(result.rewritten_query || "");
        setEvidenceStatus(result.evidence_status || "");
        setEvidenceReason(result.evidence_reason || "");
        setGroundingStatus(result.grounding_status || "");
        setGroundingReason(result.grounding_reason || "");
        setChatHistory((history) => [
          {
            id: makeHistoryId(),
            mode: "agentic",
            question: currentQuestion,
            answer: nextAnswer,
            sources: nextSources,
            document_id: requestDocumentId,
            document_name: documentName,
            createdAt: new Date().toISOString(),
            rewritten_query: result.rewritten_query,
            evidence_status: result.evidence_status,
            evidence_reason: result.evidence_reason,
            grounding_status: result.grounding_status,
            grounding_reason: result.grounding_reason,
          },
          ...history,
        ]);
      } else {
        const result = await chat(payload);
        const nextSources = result.sources ?? [];
        const nextAnswer = result.answer;

        setAnswer(nextAnswer);
        setSources(nextSources);
        setRewrittenQuery("");
        setEvidenceStatus("");
        setEvidenceReason("");
        setGroundingStatus("");
        setGroundingReason("");
        setChatHistory((history) => [
          {
            id: makeHistoryId(),
            mode: "basic",
            question: currentQuestion,
            answer: nextAnswer,
            sources: nextSources,
            document_id: requestDocumentId,
            document_name: documentName,
            createdAt: new Date().toISOString(),
          },
          ...history,
        ]);
      }
    } catch (exc) {
      setError(`问答失败: ${(exc as Error).message}`);
    } finally {
      setAnswering(false);
    }
  }

  function handleClearSelection() {
    setSelectedDocumentId(null);
    setError("");
  }

  function handleClearChat() {
    setChatHistory([]);
    setAnswer("");
    setSources([]);
    setRewrittenQuery("");
    setEvidenceStatus("");
    setEvidenceReason("");
    setGroundingStatus("");
    setGroundingReason("");
    setError("");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Edu-RAG-Agent</h1>
          <p>Course-material RAG assistant</p>
        </div>
        <div className={`status-pill ${backendOnline ? "online" : "offline"}`}>
          <span />
          {backendOnline ? "Backend online" : "Backend offline"}
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="workspace">
        <section className="left-column">
          <div className="panel">
            <div className="panel-heading">
              <h2>Upload</h2>
              <p>PDF / Markdown</p>
            </div>
            <input
              className="file-input"
              type="file"
              accept=".pdf,.md,.markdown"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
            <button className="primary-button" disabled={uploading} onClick={handleUpload}>
              {uploading ? "Uploading..." : "Upload"}
            </button>

            {uploadResult && (
              <div className="result-box">
                <dl>
                  <dt>document_id</dt>
                  <dd>{uploadResult.document_id}</dd>
                  <dt>original_filename</dt>
                  <dd>{uploadResult.original_filename}</dd>
                  <dt>file_type</dt>
                  <dd>{uploadResult.file_type}</dd>
                  <dt>status</dt>
                  <dd>{uploadResult.status}</dd>
                  <dt>stored_path</dt>
                  <dd>{uploadResult.stored_path}</dd>
                </dl>
              </div>
            )}
          </div>

          <div className="panel document-panel">
            <div className="panel-heading row-heading">
              <div>
                <h2>Documents</h2>
                <p>{loadingDocuments ? "Refreshing documents..." : `${documents.length} records`}</p>
              </div>
              <button className="ghost-button" disabled={loadingDocuments} onClick={refreshDocuments}>
                Refresh
              </button>
            </div>

            <div className="document-list">
              {documents.length === 0 && (
                <div className="empty-state">No documents yet.</div>
              )}

              {documents.map((doc) => {
                const isSelected = selectedDocumentId === doc.document_id;
                const isIndexing = indexingDocumentId === doc.document_id;
                const isDeleting = deletingDocumentId === doc.document_id;
                const indexLabel = doc.status === "indexed" ? "Re-index" : "Index";

                return (
                  <article
                    className={`document-card ${isSelected ? "selected" : ""}`}
                    key={doc.document_id}
                  >
                    <div className="document-main">
                      <h3>{doc.original_filename || doc.document_id}</h3>
                      <p>{doc.document_id}</p>
                    </div>
                    <div className="document-meta">
                      <span>{doc.file_type || "unknown"}</span>
                      <span>{doc.status || "unknown"}</span>
                      <span>{doc.chunk_count ?? 0} chunks</span>
                    </div>
                    <div className="document-footer">
                      <span>{doc.updated_at || ""}</span>
                      <div className="document-actions">
                        <button
                          className="small-button"
                          disabled={isSelected}
                          onClick={() => setSelectedDocumentId(doc.document_id)}
                        >
                          {isSelected ? "Selected" : "Select"}
                        </button>
                        <button
                          className="small-button"
                          disabled={Boolean(indexingDocumentId || deletingDocumentId)}
                          onClick={() => handleIndex(doc.document_id)}
                        >
                          {isIndexing ? "Indexing..." : indexLabel}
                        </button>
                        <button
                          className="danger-button"
                          disabled={Boolean(indexingDocumentId || deletingDocumentId)}
                          onClick={() => handleDelete(doc)}
                        >
                          {isDeleting ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="right-column">
          <div className="panel chat-panel">
            <div className="panel-heading row-heading">
              <div>
                <h2>Chat</h2>
                <p>
                  Search scope: <strong>{searchScopeLabel}</strong>
                </p>
              </div>
              {selectedDocumentId && (
                <button className="ghost-button" onClick={handleClearSelection}>
                  Clear selection
                </button>
              )}
            </div>

            {selectedDocument ? (
              <div className="selected-doc detail-grid">
                <div>
                  <dt>original_filename</dt>
                  <dd>{selectedDocument.original_filename || ""}</dd>
                </div>
                <div>
                  <dt>document_id</dt>
                  <dd>{selectedDocument.document_id}</dd>
                </div>
                <div>
                  <dt>status</dt>
                  <dd>{selectedDocument.status || "unknown"}</dd>
                </div>
              </div>
            ) : (
              <div className="scope-note">
                No document selected. The question will search across all indexed documents.
              </div>
            )}

            <div className="mode-switch">
              <div>
                <strong>Answer mode</strong>
                <p>
                  {chatMode === "agentic"
                    ? "Rewrite → Retrieve → Evidence Check → Answer → Grounding Check"
                    : "Retrieve → Answer"}
                </p>
              </div>
              <div className="mode-buttons" aria-label="Answer mode">
                <button
                  className={chatMode === "basic" ? "active" : ""}
                  type="button"
                  onClick={() => setChatMode("basic")}
                >
                  Basic RAG
                </button>
                <button
                  className={chatMode === "agentic" ? "active" : ""}
                  type="button"
                  onClick={() => setChatMode("agentic")}
                >
                  Agentic RAG
                </button>
              </div>
            </div>

            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your indexed course materials..."
            />

            <div className="chat-actions">
              <label>
                top_k
                <input
                  min={1}
                  max={20}
                  type="number"
                  value={topK}
                  onChange={(event) => setTopK(Number(event.target.value))}
                />
              </label>
              <button className="primary-button" disabled={answering} onClick={handleAsk}>
                {answering ? "Answering..." : "Ask"}
              </button>
            </div>

            {chatMode === "agentic" &&
              (rewrittenQuery || evidenceStatus || groundingStatus) && (
                <div className="agent-result">
                  <h3>Agentic Checks</h3>
                  <dl>
                    {rewrittenQuery && (
                      <div>
                        <dt>Rewritten query</dt>
                        <dd>{rewrittenQuery}</dd>
                      </div>
                    )}
                    {evidenceStatus && (
                      <div>
                        <dt>Evidence status</dt>
                        <dd>
                          <span className={`status-badge ${statusClassName(evidenceStatus)}`}>
                            {evidenceStatus}
                          </span>
                        </dd>
                      </div>
                    )}
                    {evidenceReason && (
                      <div>
                        <dt>Evidence reason</dt>
                        <dd>{evidenceReason}</dd>
                      </div>
                    )}
                    {groundingStatus && (
                      <div>
                        <dt>Grounding status</dt>
                        <dd>
                          <span className={`status-badge ${statusClassName(groundingStatus)}`}>
                            {groundingStatus}
                          </span>
                        </dd>
                      </div>
                    )}
                    {groundingReason && (
                      <div>
                        <dt>Grounding reason</dt>
                        <dd>{groundingReason}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}

            {answer && (
              <div className="answer-box">
                <h3>Latest Answer</h3>
                <p>{answer}</p>
              </div>
            )}
          </div>

          <div className="panel sources-panel">
            <div className="panel-heading">
              <h2>Sources</h2>
              <p>{sources.length} items</p>
            </div>

            {sources.length === 0 && <div className="empty-state">No sources yet.</div>}

            <div className="source-list">
              {sources.map((source, index) => (
                <article className="source-card" key={`${source.document_id}-${index}`}>
                  <h3>Source {index + 1}</h3>
                  <dl>
                    {sourceFields(source).map(([label, value]) => (
                      <div key={label}>
                        <dt>{label}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </article>
              ))}
            </div>
          </div>

          <div className="panel history-panel">
            <div className="panel-heading row-heading">
              <div>
                <h2>Chat History</h2>
                <p>{chatHistory.length} records</p>
              </div>
              <button
                className="ghost-button"
                disabled={chatHistory.length === 0}
                onClick={handleClearChat}
              >
                Clear chat
              </button>
            </div>

            {chatHistory.length === 0 && (
              <div className="empty-state">No chat history yet.</div>
            )}

            <div className="history-list">
              {chatHistory.map((item) => (
                <article className="history-card" key={item.id}>
                  <div className="history-meta">
                    <span className="mode-label">{modeLabel(item.mode)}</span>
                    <span>{item.document_name || "All indexed documents"}</span>
                    <span>{formatDate(item.createdAt)}</span>
                    <span>{item.sources.length} sources</span>
                  </div>
                  <h3>{item.question}</h3>
                  {item.mode === "agentic" && (
                    <div className="history-checks">
                      {item.rewritten_query && <span>query: {item.rewritten_query}</span>}
                      {item.evidence_status && (
                        <span>evidence: {item.evidence_status}</span>
                      )}
                      {item.grounding_status && (
                        <span>grounding: {item.grounding_status}</span>
                      )}
                    </div>
                  )}
                  <p>{item.answer}</p>
                  {item.sources.length > 0 && (
                    <ul>
                      {item.sources.slice(0, 3).map((source, index) => (
                        <li key={`${item.id}-${index}`}>{sourceSummary(source)}</li>
                      ))}
                    </ul>
                  )}
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
