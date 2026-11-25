from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from code_review_harness.clients.base import LLMClient
from code_review_harness.chunking import format_snippet_for_prompt
from code_review_harness.models import ReviewFinding, Severity, Category
from code_review_harness.models import FileSnippet


class ReviewPass(ABC):
    name: str
    category: Category

    @abstractmethod
    def system_prompt(self) -> str: ...

    def build_user_prompt(self, chunk: FileSnippet, repo_context: str) -> str:
        return (
            f"Repository context: {repo_context}\n\n"
            f"Review the following code chunk. Return ONLY valid JSON.\n\n"
            f"{format_snippet_for_prompt(chunk)}"
        )

    def run(
        self,
        client: LLMClient,
        chunk: FileSnippet,
        repo_context: str,
    ) -> tuple[list[ReviewFinding], str]:
        data = client.chat_json(
            self.system_prompt(),
            self.build_user_prompt(chunk, repo_context),
        )
        findings = _parse_findings(data, self.category, chunk.path)
        summary = str(data.get("chunk_summary", "") or "")
        return findings, summary


def _parse_findings(
    data: dict,
    default_category: Category,
    default_file: str,
) -> list[ReviewFinding]:
    raw = data.get("findings") or []
    if not isinstance(raw, list):
        return []
    out: list[ReviewFinding] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            sev = _parse_severity(str(item.get("severity", "info")))
            cat = item.get("category", default_category)
            if cat not in ("security", "bug", "quality", "best_practice"):
                cat = default_category
            out.append(
                ReviewFinding(
                    category=cat,
                    severity=sev,
                    file=str(item.get("file") or default_file),
                    line_start=int(item.get("line_start", 1)),
                    line_end=int(item.get("line_end", item.get("line_start", 1))),
                    title=str(item.get("title", "Issue")[:200]),
                    description=str(item.get("description", ""))[:4000],
                    recommendation=str(item.get("recommendation", ""))[:2000],
                )
            )
        except (TypeError, ValueError):
            continue
    return out


def _parse_severity(value: str) -> Severity:
    v = value.lower().strip()
    for sev in Severity:
        if sev.value == v:
            return sev
    return Severity.INFO


def _prompt_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "prompts" / f"{name}.md"


def load_prompt(name: str, fallback: str) -> str:
    path = _prompt_path(name)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return fallback