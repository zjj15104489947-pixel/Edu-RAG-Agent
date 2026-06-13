"""LLM utilities for creating the project chat model."""

import os
from functools import lru_cache

from langchain_deepseek import ChatDeepSeek

from core.config import get_settings


@lru_cache
def get_chat_model() -> ChatDeepSeek:
    """Create and cache the DeepSeek chat model used by the project."""
    settings = get_settings()

    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置，请在 .env 中填写 DeepSeek API key。")
    
    os.environ["DEEPSEEK_API_KEY"] = settings.llm_api_key

    return ChatDeepSeek(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0,
        max_retries=2,
    )
