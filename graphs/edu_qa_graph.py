""" Synchronous LangGraph workflow for Agentic RAG question answering.
    同步版 LangGraph 工作流
"""

from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph

from core.llm import get_chat_model
from services.qa_service import build_sources, format_context, retrieve_relevant_chunks

# 定义 LangGraph 的共享状态
class AgentQAState(TypedDict, total=False):
    """State passed through the EduRAG Agentic QA graph."""

    question: str
    document_id: str | None
    top_k: int

    rewritten_query: str  # query rewrite 节点输出的检索 query

    retrieved_docs: list[Document]  # Chroma 检索到的 Document chunks
    context: str  # 拼给 LLM 的资料上下文
    sources: list[dict]  # 返回给前端展示的来源信息

    evidence_status: str
    evidence_reason: str

    answer: str  # 最终答案

    grounding_status: str
    grounding_reason: str

# 把 LLM 返回结果转成字符串
def _to_text(response) -> str:
    """Convert an LLM response to plain text."""

    content = getattr(response, "content", None)
    if content is not None:
        return str(content).strip()
    return str(response).strip()


# 同步调用 LLM
def _invoke_llm(prompt: str) -> str:
    """Invoke the project chat model and return plain text."""

    llm = get_chat_model()
    response = llm.invoke(prompt)
    return _to_text(response)


# 拿 LLM 输出里的第一行非空内容
def _first_nonempty_line(text: str) -> str:
    """Return the first non-empty line from a text block."""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


# 拿第一行之后的内容作为 reason
def _remaining_lines(text: str) -> str:
    """Return text after the first line, or an empty string."""

    lines = text.splitlines()
    if len(lines) <= 1:
        return ""
    return "\n".join(lines[1:]).strip()


# 节点一：查询改写
def rewrite_query_node(state: AgentQAState) -> dict:
    """Rewrite the user question into a retrieval-friendly query."""

    question = state.get("question", "")
    prompt = f"""你是一个检索查询改写器。
请把用户问题改写成适合在课程教材 chunk 中进行语义检索的 query。
如果用户问题是中文，且可能要检索英文教材，请改写成英文 query。
如果用户问题已经是英文，请保留核心含义并略微优化。
只输出改写后的 query，不要解释。

用户问题：
{question}
"""

    try:
        rewritten_query = _invoke_llm(prompt).strip()
    except Exception:
        rewritten_query = ""

    if not rewritten_query:
        rewritten_query = question

    return {"rewritten_query": rewritten_query}


# 节点二：检索
def retrieve_node(state: AgentQAState) -> dict:
    """Retrieve relevant chunks using the baseline QA retrieval utilities."""

    query = state.get("rewritten_query") or state.get("question", "")
    docs = retrieve_relevant_chunks(
        question=query,
        document_id=state.get("document_id"),
        top_k=state.get("top_k"),
    )

    return {
        "retrieved_docs": docs, # 原始 Document 列表
        "context": format_context(docs), # 拼好的上下文
        "sources": build_sources(docs), # 来源信息
    }

# 节点三：证据充分性检查
def check_evidence_node(state: AgentQAState) -> dict:
    """Check whether retrieved context is sufficient for the question."""

    question = state.get("question", "")
    rewritten_query = state.get("rewritten_query", "")
    context = state.get("context", "")

    if len(context.strip()) < 50:
        return {
            "evidence_status": "INSUFFICIENT",
            "evidence_reason": "No enough retrieved context.",
        }

    prompt = f"""你是一个 RAG 系统中的证据充分性评估器。

你的任务不是判断 context 是否包含完美、完整、教科书式答案，
而是判断 context 是否足够支持一个基于资料的、有边界说明的回答。

判断标准：

输出 SUFFICIENT，当：
- context 与 question / rewritten_query 高度相关；
- context 包含能支持基础回答的概念、事实、描述或解释；
- 即使 context 不够完整，但足以回答主要问题并说明依据有限；
- 对定义类问题，只要 context 中有相关概念和解释片段，可以支持一个基础定义。

输出 INSUFFICIENT，当：
- context 为空或极短；
- context 与问题主题明显无关；
- context 只是孤立提到关键词，但没有任何可用于解释或回答的内容；
- 用户问的问题超出资料范围，例如问量子计算 Shor 算法，而 context 只是计算机网络内容。

第一行只能输出 SUFFICIENT 或 INSUFFICIENT。
第二行开始简要说明原因。

question:
{question}

rewritten_query:
{rewritten_query}

context:
{context}
"""

    try:
        response_text = _invoke_llm(prompt)
    except Exception as exc:
        return {
            "evidence_status": "INSUFFICIENT",
            "evidence_reason": f"Evidence check failed: {exc}",
        }

    first_line = _first_nonempty_line(response_text).upper()
    reason = _remaining_lines(response_text) or response_text

    if first_line.startswith("INSUFFICIENT"):
        status = "INSUFFICIENT"
    elif first_line.startswith("SUFFICIENT"):
        status = "SUFFICIENT"
    else:
        status = "INSUFFICIENT"
        reason = response_text

    return {
        "evidence_status": status,
        "evidence_reason": reason.strip(),
    }


# 节点四：生成答案
def generate_answer_node(state: AgentQAState) -> dict:
    """Generate an answer based on retrieved context and evidence status."""

    question = state.get("question", "")
    context = state.get("context", "")

    if state.get("evidence_status") == "INSUFFICIENT":
        return {
            "answer": (
                "根据当前已索引资料，未检索到足够依据回答该问题。"
                "建议换一种问法、提高 top_k，或上传/索引更相关的课程资料。"
            )
        }

    prompt = f"""你是一个严谨的课程教材学习助手。
你必须基于 context 回答 question，不要编造资料中没有的内容。
如果 context 只支持部分回答，也应回答可以由资料支持的部分，并明确说明“根据当前检索片段，依据有限”。
不要因为资料不完整就完全拒答，除非 evidence_status 是 INSUFFICIENT。
回答语言必须尽量与用户问题一致：中文问题用中文回答，英文问题用英文回答。

不要使用 Markdown 语法：
- 不要使用 # 或 ### 标题
- 不要使用 **加粗**
- 不要使用 Markdown 表格

请使用纯文本编号格式：
如果 question 是英文，使用：
1. Direct answer:
2. Evidence from the document:
3. Notes:

如果 question 是中文，使用：
1. 直接回答：
2. 教材依据：
3. 易错点或补充说明：

question:
{question}

context:
{context}
"""

    answer = _invoke_llm(prompt)
    return {"answer": answer}


# 节点五：检查答案是否被检索材料支撑
def check_grounding_node(state: AgentQAState) -> dict:
    """Check whether the generated answer is grounded in retrieved context."""

    answer = state.get("answer", "")
    context = state.get("context", "")

    if state.get("evidence_status") == "INSUFFICIENT" or "未检索到足够依据" in answer:
        return {
            "grounding_status": "GROUNDED",
            "grounding_reason": "The answer correctly states that evidence is insufficient.",
        }

    prompt = f"""你是一个严格的 groundedness 检查器。
请判断 answer 中的主要事实是否被 context 支撑。
如果主要事实均能从 context 中得到支持，输出 GROUNDED。
如果 answer 包含 context 未支持的事实、推断或编造内容，输出 UNGROUNDED。
第一行只能输出 GROUNDED 或 UNGROUNDED。
第二行开始简要说明原因。

context:
{context}

answer:
{answer}
"""

    try:
        response_text = _invoke_llm(prompt)
    except Exception as exc:
        return {
            "grounding_status": "UNGROUNDED",
            "grounding_reason": f"Grounding check failed: {exc}",
        }

    first_line = _first_nonempty_line(response_text).upper()
    reason = _remaining_lines(response_text) or response_text

    if first_line.startswith("UNGROUNDED"):
        status = "UNGROUNDED"
    elif first_line.startswith("GROUNDED"):
        status = "GROUNDED"
    else:
        status = "UNGROUNDED"
        reason = response_text

    return {
        "grounding_status": status,
        "grounding_reason": reason.strip(),
    }


# 创建并编译 LangGraph
def build_edu_qa_graph():
    """Build and compile the synchronous EduRAG Agentic QA graph."""

    graph = StateGraph(AgentQAState)
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("check_evidence", check_evidence_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("check_grounding", check_grounding_node)

    graph.add_edge(START, "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("retrieve", "check_evidence")
    graph.add_edge("check_evidence", "generate_answer")
    graph.add_edge("generate_answer", "check_grounding")
    graph.add_edge("check_grounding", END)

    return graph.compile()
