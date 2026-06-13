# Edu-RAG-Agent

Edu-RAG-Agent 是一个面向课程资料的本地 Agentic RAG 知识库问答原型，用于学习和实习项目展示。用户可以上传 PDF 或 Markdown，建立本地向量索引，并在 Basic RAG 与 LangGraph Agentic RAG 两种模式下提问和查看来源。

这是一个可本地运行的 v0 原型，不是生产级、高并发或大规模知识库系统。

## 核心能力

- PDF 文本层提取与 Markdown 读取
- LangChain `Document` 与递归文本切分
- BAAI/bge-m3 本地 embedding
- Chroma 本地向量库
- SQLite document registry
- 文档上传、索引、重建索引和删除
- 基础 RAG：检索后直接生成答案
- Agentic RAG：查询改写、检索、证据检查、答案生成、grounding 检查
- sources 元数据溯源
- FastAPI 后端与 React/Vite 前端
- 前端本地 chat history，不写入后端

## 系统流程

文档流程：

```text
PDF / Markdown
→ 上传与 registry 登记
→ LangChain Document
→ chunks
→ BGE-M3 embedding
→ Chroma
```

Basic RAG：

```text
question → retrieve → answer → sources
```

Agentic RAG：

```text
question
→ query rewrite
→ retrieve
→ evidence check
→ answer generation
→ grounding check
→ answer + sources + checks
```

## 项目结构

```text
backend/     FastAPI 应用、schemas 与 routes
core/        配置和 DeepSeek 模型初始化
graphs/      LangGraph Agentic RAG workflow
loaders/     PDF / Markdown 读取
rag/         chunking、embedding、Chroma、prompt
services/    文档生命周期和问答业务逻辑
scripts/     本地调试命令
frontend/    Vite + React + TypeScript 前端
data/        本地运行数据，不提交教材、上传文件、registry 或向量库
```

## 环境要求

- Python 3.10+
- Node.js 18+
- DeepSeek API Key
- 首次使用 BGE-M3 时需要下载模型，磁盘占用和加载时间都较大

## 后端启动

创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中填写：

```env
LLM_API_KEY=your_deepseek_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

启动后端：

```powershell
uvicorn backend.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 前端启动

后端启动后，打开另一个终端：

```powershell
cd frontend
npm install
npm run dev
```

如果 PowerShell 因执行策略阻止 `npm.ps1`，可以改用：

```powershell
npm.cmd install
npm.cmd run dev
```

访问：

```text
http://localhost:5173
```

Vite 会把 `/api/*` 代理到 `http://127.0.0.1:8000`。

## 主要 API

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

项目还保留 `POST /documents/index-local` 供本机调试，它可以读取服务进程可访问的本地路径，不应作为公开生产接口暴露。

`POST /chat` 是基础 RAG baseline，返回 `answer + sources`。

`POST /agent/chat` 是同步 LangGraph 增强接口，额外返回：

- `rewritten_query`
- `evidence_status` / `evidence_reason`
- `grounding_status` / `grounding_reason`

## 本地命令行调试

把自己的 PDF 或 Markdown 放到本地目录后，可以运行：

```powershell
python scripts/inspect_pdf.py <path-to-document.pdf>
python scripts/inspect_markdown.py <path-to-document.md>
python scripts/ingest_document.py <path-to-document.pdf>
python scripts/list_documents.py
python scripts/query_index.py "what is packet switching?" --document-id <document_id>
python scripts/ask_document.py "what is packet switching?" --document-id <document_id>
```

仓库不包含教材 PDF/Markdown。请只使用你有权使用的资料。

## 推荐演示流程

1. 打开前端并确认 Backend online。
2. 上传一个 PDF 或 Markdown。
3. 点击 Index，确认状态变为 `indexed` 且 `chunk_count > 0`。
4. 选择 Basic RAG 提问并查看 answer 与 sources。
5. 选择 Agentic RAG 提问并查看 rewritten query、evidence 和 grounding 检查。
6. 用明显超出资料范围的问题验证系统会说明证据不足。
7. 删除文档，确认 registry、向量 chunks 和上传文件被清理。

## 本地数据与 Git

以下内容不会提交到 Git：

- `.env` 和 API Key
- `.venv/`、`.cache/`
- `data/raw/uploads/`
- `data/raw/*.pdf`、`data/raw/*.md`
- `data/processed/`
- `data/chroma_db/`
- `frontend/node_modules/`、`frontend/dist/`

## 当前限制

- 主要支持具有文本层的 PDF 和 UTF-8 Markdown
- 扫描版 PDF 尚未接入 OCR / MinerU
- 索引和问答是同步执行，大文件或 CPU embedding 会较慢
- BGE-M3 首次下载及本地加载成本较高
- SQLite 与本地 Chroma 适合单机演示，不面向多实例并发
- Agentic RAG 当前是线性 workflow，没有 conditional edge、answer rewrite 或 streaming
- 没有用户、权限、任务队列和自动化评测体系

## 后续方向

- 增加 retrieval / grounding 自动化评测
- 后台索引任务与状态轮询
- LangGraph conditional edge 和 answer rewrite
- 更完善的文档去重、索引版本与失败恢复
- 可插拔 MinerU / OCR 预处理适配层
