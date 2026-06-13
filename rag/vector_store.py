"""根据配置，创建一个 Chroma 向量数据库连接。如果数据库目录不存在就自动创建，
然后把之前加载好的 Embedding 模型挂上去，让 Chroma 知道怎么把文字变成向量"""

from pathlib import Path
from langchain_chroma import Chroma

from core.config import get_settings
from rag.embeddings import get_embedding_model

def get_vector_store() -> Chroma:
    """Create a Chroma vector store using project settings."""
    settings = get_settings()

    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True,exist_ok=True)

    embedding_model = get_embedding_model()

    return Chroma(
        collection_name=settings.chroma_collection,
        persist_directory=str(persist_dir),
        embedding_function=embedding_model,
    )

