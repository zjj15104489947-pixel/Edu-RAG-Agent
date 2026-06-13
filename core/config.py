"""集中管理项目配置，从环境变量和 .env 文件读取模型、路径等设置。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM settings
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # Embedding settings
    embedding_provider: str = "local"  # 用本地模型还是云端API
    embedding_model: str = "BAAI/bge-m3"  # 具体模型
    embedding_device: str = "cpu"  # 跑在CPU还是GPU("cuda")
    normalize_embeddings: bool = True  # 归一化，把向量长度缩放到 1，这样检索时用余弦相似度更稳定，不同长度文本可比
    model_cache_dir: str = ".cache/huggingface"  # HuggingFace 模型下载后存储位置(避免每次重新下载)
    hf_endpoint: str = "https://hf-mirror.com"  # 国内镜像站(可选填)
    hf_hub_disable_symlinks_warning: bool = True  # 关闭 Windows 下软链接 warning

    hf_hub_offline: bool = False
    transformers_offline: bool = False
    embedding_local_files_only: bool = False
    
    # Data paths
    data_dir: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    document_registry_db: str = "data/processed/document_registry.sqlite"
    document_upload_dir: str = "data/raw/uploads"
    
    # Chroma settings
    chroma_persist_dir: str = "data/chroma_db"  # 向量库持久化目录
    chroma_collection: str = "edu_rag_networking"  # 集合名

    # RAG parameters
    chunk_size: int = 800
    chunk_overlap: int = 100
    retrieval_top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",  # 从项目根目录的 .env 文件加载环境变量
        env_file_encoding="utf-8",  # .env 文件用 UTF-8 编码
        extra="ignore",  # 如果 .env 里有这个类没定义的字段，忽略不报错
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
