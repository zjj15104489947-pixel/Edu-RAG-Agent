"""初始化并返回一个 HuggingFace 文本向量化模型，且只初始化一次，之后直接复用"""
import os
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from core.config import get_settings

@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Create and cache the embedding model used by the RAG pipeline."""

    settings=get_settings()
    if settings.embedding_provider != "local":
        raise ValueError(
            f"当前只支持本地 embedding 模型，收到：{settings.embedding_provider}"
        )
    
    if settings.hf_endpoint:
        os.environ["HF_ENDPOINT"] = settings.hf_endpoint

    if settings.hf_hub_disable_symlinks_warning:
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    if settings.hf_hub_offline:
        os.environ["HF_HUB_OFFLINE"] = "1"

    if settings.transformers_offline:
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    model_kwargs = {
        "device": settings.embedding_device,
    }

    if settings.embedding_local_files_only:
        model_kwargs["local_files_only"] = True

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs=model_kwargs,
        encode_kwargs={
            "normalize_embeddings": settings.normalize_embeddings,
        },
        cache_folder=settings.model_cache_dir,
    )