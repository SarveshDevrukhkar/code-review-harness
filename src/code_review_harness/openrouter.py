"""Backward-compatible re-export; prefer code_review_harness.clients."""

from code_review_harness.clients.http_chat import HttpChatClient
from code_review_harness.clients.openrouter import create_openrouter_client

OpenRouterClient = HttpChatClient  # legacy name; use create_openrouter_client(config)

__all__ = ["OpenRouterClient", "create_openrouter_client"]