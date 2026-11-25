from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from code_review_harness.models import LLMProvider, ReviewConfig

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
}

DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434/v1"
DEFAULT_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def load_env(path: Path | None = None) -> None:
    root = Path.cwd()
    env_path = path or root / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def _parse_provider(raw: str) -> LLMProvider:
    value = raw.strip().lower()
    if value in ("local", "ollama"):
        return LLMProvider.LOCAL
    if value in ("remote", "openrouter"):
        return LLMProvider.REMOTE
    raise ValueError(
        f'Invalid LLM_PROVIDER "{raw}". Use "local" (Ollama) or "remote" (OpenRouter).'
    )


def validate_config(provider_override: str | None = None) -> ReviewConfig:
    load_env()

    provider_raw = provider_override or os.getenv("LLM_PROVIDER", "remote")
    provider = _parse_provider(provider_raw)

    max_file_bytes = int(os.getenv("REVIEW_MAX_FILE_BYTES", "500000"))
    max_chunk_lines = int(os.getenv("REVIEW_MAX_CHUNK_LINES", "400"))
    temperature = float(os.getenv("REVIEW_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("REVIEW_MAX_TOKENS", "4096"))

    if provider == LLMProvider.LOCAL:
        base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE).strip().rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "").strip() or os.getenv("OPENROUTER_MODEL", "").strip()
        if not model:
            raise ValueError(
                "OLLAMA_MODEL is not set. Example: OLLAMA_MODEL=llama3.2 "
                "(see .env.example)."
            )
        timeout = float(os.getenv("OLLAMA_TIMEOUT_SEC", os.getenv("REVIEW_LLM_TIMEOUT_SEC", "300")))
        return ReviewConfig(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key="",
            max_file_bytes=max_file_bytes,
            max_chunk_lines=max_chunk_lines,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_sec=timeout,
        )

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env or use LLM_PROVIDER=local."
        )
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    if not model:
        raise ValueError("OPENROUTER_MODEL must not be empty.")
    base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE).strip().rstrip("/")
    timeout = float(os.getenv("OPENROUTER_TIMEOUT_SEC", os.getenv("REVIEW_LLM_TIMEOUT_SEC", "120")))

    return ReviewConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        max_file_bytes=max_file_bytes,
        max_chunk_lines=max_chunk_lines,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_sec=timeout,
    )