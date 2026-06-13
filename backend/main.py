""" FastAPI backend entry point for Edu-RAG-Agent.
    FastAPI 应用入口
"""

from fastapi import FastAPI

from backend.routes import agent_chat, chat, documents


app = FastAPI(
    title="Edu-RAG-Agent API",
    description="Backend API for course-material RAG question answering.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    """Return API health status."""

    return {"status": "ok"}

# 把其他文件接口注册到主应用
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(agent_chat.router)
