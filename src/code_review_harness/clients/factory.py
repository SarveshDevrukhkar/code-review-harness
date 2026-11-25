from __future__ import annotations

from code_review_harness.clients.base import LLMClient
from code_review_harness.clients.ollama import create_ollama_client
from code_review_harness.clients.openrouter import create_openrouter_client
from code_review_harness.models import LLMProvider, ReviewConfig


def get_client(config: ReviewConfig) -> LLMClient:
    if config.provider == LLMProvider.LOCAL:
        return create_ollama_client(config)
    if config.provider == LLMProvider.REMOTE:
        return create_openrouter_client(config)
    raise ValueError(f"Unknown LLM provider: {config.provider}")