from __future__ import annotations

from code_review_harness.models import FileSnippet, ReviewConfig

PRIORITY_KEYWORDS = (
    "auth", "login", "password", "secret", "token", "crypto", "cipher",
    "sql", "query", "admin", "payment", "jwt", "oauth", "session",
)


def _priority_score(path: str) -> int:
    lower = path.lower()
    return sum(1 for kw in PRIORITY_KEYWORDS if kw in lower)


def chunk_snippet(snippet: FileSnippet, config: ReviewConfig) -> list[FileSnippet]:
    lines = snippet.content.splitlines()
    if len(lines) <= config.max_chunk_lines:
        return [snippet]

    chunks: list[FileSnippet] = []
    overlap = min(20, config.max_chunk_lines // 10)
    step = config.max_chunk_lines - overlap
    i = 0
    while i < len(lines):
        block = lines[i : i + config.max_chunk_lines]
        start = snippet.start_line + i
        chunks.append(
            FileSnippet(
                path=snippet.path,
                language=snippet.language,
                content="\n".join(block),
                start_line=start,
                change_type=snippet.change_type,
            )
        )
        if i + config.max_chunk_lines >= len(lines):
            break
        i += step
    return chunks


def expand_and_prioritize(
    snippets: list[FileSnippet],
    config: ReviewConfig,
) -> list[FileSnippet]:
    all_chunks: list[FileSnippet] = []
    for sn in snippets:
        all_chunks.extend(chunk_snippet(sn, config))
    all_chunks.sort(key=lambda s: (-_priority_score(s.path), s.path, s.start_line))
    return all_chunks


def format_snippet_for_prompt(chunk: FileSnippet) -> str:
    lines = chunk.content.splitlines()
    numbered = []
    for idx, line in enumerate(lines):
        lineno = chunk.start_line + idx
        numbered.append(f"{lineno:6d}| {line}")
    header = f"File: {chunk.path} ({chunk.language})"
    if chunk.change_type:
        header += f" [change: {chunk.change_type}]"
    return header + "\n" + "\n".join(numbered)