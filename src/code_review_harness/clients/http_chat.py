from __future__ import annotations

import json
import time
from typing import Any, Callable

import httpx

from code_review_harness.clients.base import parse_json_content
from code_review_harness.models import ReviewConfig


class HttpChatClient:
    """Shared OpenAI-style chat/completions HTTP logic."""

    def __init__(
        self,
        config: ReviewConfig,
        *,
        provider_name: str,
        error_prefix: str,
        build_headers: Callable[[], dict[str, str]],
        use_json_response_format: bool = True,
        retry_without_json_format: bool = False,
    ) -> None:
        self.config = config
        self.provider_name = provider_name
        self.error_prefix = error_prefix
        self._build_headers = build_headers
        self.use_json_response_format = use_json_response_format
        self.retry_without_json_format = retry_without_json_format
        self._usage: dict[str, Any] = {"prompt_tokens": 0, "completion_tokens": 0}

    @property
    def usage(self) -> dict[str, Any]:
        return dict(self._usage)

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                return self._post_chat(url, system, user, json_mode=self.use_json_response_format)
            except _JsonFormatRejected:
                if self.retry_without_json_format:
                    try:
                        return self._post_chat(url, system, user, json_mode=False)
                    except Exception as e:
                        last_err = e
                else:
                    last_err = _JsonFormatRejected("json_object not supported")
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, httpx.ConnectError) as e:
                last_err = e
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
        raise RuntimeError(f"{self.error_prefix}: {last_err}") from last_err

    def _post_chat(
        self,
        url: str,
        system: str,
        user: str,
        *,
        json_mode: bool,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(self.config.timeout_sec)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=self._build_headers(), json=body)
        except httpx.ConnectError as e:
            raise httpx.ConnectError(str(e)) from e

        if json_mode and self.retry_without_json_format and resp.status_code == 400:
            detail = resp.text.lower()
            if "response_format" in detail or "json" in detail:
                raise _JsonFormatRejected(resp.text)

        if resp.status_code == 404:
            raise RuntimeError(
                f'{self.error_prefix}: model "{self.config.model}" not found (HTTP 404). '
                f"For Ollama, run: ollama pull {self.config.model}"
            )

        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        resp.raise_for_status()

        data = resp.json()
        usage = data.get("usage") or {}
        self._usage["prompt_tokens"] = self._usage.get("prompt_tokens", 0) + int(
            usage.get("prompt_tokens", 0)
        )
        self._usage["completion_tokens"] = self._usage.get("completion_tokens", 0) + int(
            usage.get("completion_tokens", 0)
        )
        content = data["choices"][0]["message"]["content"]
        return parse_json_content(content)


class _JsonFormatRejected(Exception):
    pass