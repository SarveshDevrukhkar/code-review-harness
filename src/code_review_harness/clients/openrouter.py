from __future__ import annotations

from code_review_harness.clients.http_chat import HttpChatClient
from code_review_harness.models import LLMProvider, ReviewConfig


def create_openrouter_client(config: ReviewConfig) -> HttpChatClient:
    if config.provider != LLMProvider.REMOTE:
        raise ValueError("OpenRouter client requested but provider is not remote")

    def headers() -> dict[str, str]:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": config.http_referer,
            "X-Title": config.app_title,
        }

    return HttpChatClient(
        config,
        provider_name="OpenRouter",
        error_prefix="OpenRouter request failed",
        build_headers=headers,
        use_json_response_format=True,
        retry_without_json_format=False,
    )