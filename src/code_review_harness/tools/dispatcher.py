from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from code_review_harness.collector import read_snippet


@dataclass
class ReviewToolContext:
    root: Path

    def resolve(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise PermissionError("Path escapes review root")
        return p


def dispatch_tool(ctx: ReviewToolContext, name: str, arguments: dict) -> str:
    if name == "get_file_snippet":
        return _get_file_snippet(ctx, arguments)
    if name == "list_directory":
        return _list_directory(ctx, arguments)
    if name == "search_code":
        return _search_code(ctx, arguments)
    raise ValueError(f"Unknown tool: {name}")


def _get_file_snippet(ctx: ReviewToolContext, args: dict) -> str:
    fp = ctx.resolve(str(args["path"]))
    if not fp.is_file():
        return "Error: not a file"
    start = int(args.get("start_line", 1))
    end = int(args.get("end_line", start + 200))
    sn = read_snippet(fp)
    if not sn:
        return "Error: unreadable"
    lines = sn.content.splitlines()
    start_i = max(0, start - 1)
    end_i = min(len(lines), end)
    block = []
    for i in range(start_i, end_i):
        block.append(f"{i + 1:6d}| {lines[i]}")
    return "\n".join(block)


def _list_directory(ctx: ReviewToolContext, args: dict) -> str:
    rel = str(args.get("path", "."))
    glob_pat = args.get("glob")
    base = ctx.resolve(rel)
    if not base.is_dir():
        return "Error: not a directory"
    paths: list[str] = []
    if glob_pat:
        for p in sorted(base.rglob(glob_pat.lstrip("/"))):
            if p.is_file():
                paths.append(str(p.relative_to(ctx.root)))
    else:
        for p in sorted(base.iterdir()):
            paths.append(p.name + ("/" if p.is_dir() else ""))
    return "\n".join(paths[:500])


def _search_code(ctx: ReviewToolContext, args: dict) -> str:
    pattern = str(args["pattern"])
    max_results = int(args.get("max_results", 50))
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"Error: invalid regex: {e}"
    hits: list[str] = []
    for p in ctx.root.rglob("*"):
        if not p.is_file() or p.stat().st_size > 200_000:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if rx.search(line):
                rel = p.relative_to(ctx.root)
                hits.append(f"{rel}:{i}: {line.strip()[:200]}")
                if len(hits) >= max_results:
                    return "\n".join(hits)
    return "\n".join(hits) or "(no matches)"