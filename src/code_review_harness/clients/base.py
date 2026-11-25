from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    provider_name: str

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        max_retries: int = 3,
    ) -> dict[str, Any]: ...

    @property
    def usage(self) -> dict[str, Any]: ...


def parse_json_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    return json.loads(content)