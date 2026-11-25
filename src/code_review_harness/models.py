from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


Category = Literal["security", "bug", "quality", "best_practice"]


class LLMProvider(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


@dataclass
class ReviewConfig:
    provider: LLMProvider
    model: str
    base_url: str
    api_key: str = ""
    max_file_bytes: int = 500_000
    max_chunk_lines: int = 400
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_sec: float = 300.0
    app_title: str = "code-review-harness"
    http_referer: str = "https://localhost"

    @property
    def provider_label(self) -> str:
        return "Ollama" if self.provider == LLMProvider.LOCAL else "OpenRouter"

    @property
    def backend_display(self) -> str:
        prefix = "ollama" if self.provider == LLMProvider.LOCAL else "openrouter"
        return f"{prefix}:{self.model}"


@dataclass
class FileSnippet:
    path: str
    language: str
    content: str
    start_line: int = 1
    change_type: str | None = None  # added, modified, deleted, context


@dataclass
class ReviewFinding:
    category: Category
    severity: Severity
    file: str
    line_start: int
    line_end: int
    title: str
    description: str
    recommendation: str
    source: Literal["llm", "static"] = "llm"

    def dedupe_key(self) -> tuple:
        return (self.file, self.line_start, self.title.lower().strip())


@dataclass
class ReviewReport:
    scope: str
    summary: str
    overall_risk: str
    findings: list[ReviewFinding] = field(default_factory=list)
    files_reviewed: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    model: str = ""
    backend: str = ""
    usage: dict[str, Any] = field(default_factory=dict)

    def counts_by_severity(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.findings:
            key = f.severity.value
            out[key] = out.get(key, 0) + 1
        return out