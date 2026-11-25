from __future__ import annotations

import httpx

from code_review_harness.clients.http_chat import HttpChatClient
from code_review_harness.models import LLMProvider, ReviewConfig


def verify_ollama_reachable(config: ReviewConfig) -> None:
    """Fail fast if Ollama is not running (no remote fallback)."""
    root = config.base_url.rstrip("/")
    if root.endswith("/v1"):
        tags_url = root[: -len("/v1")] + "/api/tags"
    else:
        tags_url = root + "/api/tags"
    try:
        with httpx.Client(timeout=min(config.timeout_sec, 30.0)) as client:
            resp = client.get(tags_url)
        if resp.status_code >= 500:
            raise RuntimeError(
                f"Failed to connect to local LLM (Ollama at {config.base_url}): "
                f"tags endpoint returned HTTP {resp.status_code}"
            )
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"Failed to connect to local LLM (Ollama at {config.base_url}): "
            f"is `ollama serve` running? ({e})"
        ) from e
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"Failed to connect to local LLM (Ollama at {config.base_url}): {e}"
        ) from e


def create_ollama_client(config: ReviewConfig) -> HttpChatClient:
    if config.provider != LLMProvider.LOCAL:
        raise ValueError("Ollama client requested but provider is not local")
    verify_ollama_reachable(config)

    def headers() -> dict[str, str]:
        return {"Content-Type": "application/json"}

    return HttpChatClient(
        config,
        provider_name="Ollama",
        error_prefix=f"Failed to call local LLM (Ollama at {config.base_url})",
        build_headers=headers,
        use_json_response_format=True,
        retry_without_json_format=True,
    )