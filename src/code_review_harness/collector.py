from __future__ import annotations

import subprocess
from pathlib import Path

from code_review_harness.config import DEFAULT_IGNORE_DIRS
from code_review_harness.models import FileSnippet, ReviewConfig

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
    ".gz", ".tar", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".class",
}

LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".sql": "sql",
    ".sh": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".vue": "vue",
    ".swift": "swift",
}


def detect_language(path: Path) -> str:
    return LANG_BY_EXT.get(path.suffix.lower(), "text")


def _should_skip_dir(name: str) -> bool:
    return name in DEFAULT_IGNORE_DIRS or name.startswith(".")


def discover_files(
    target: Path,
    config: ReviewConfig,
    extensions: set[str] | None = None,
) -> tuple[list[Path], list[str]]:
    target = target.resolve()
    reviewed: list[Path] = []
    skipped: list[str] = []

    if target.is_file():
        ok, reason = _file_eligible(target, config, extensions)
        if ok:
            reviewed.append(target)
        else:
            skipped.append(f"{target}: {reason}")
        return reviewed, skipped

    for root, dirs, files in os_walk_sorted(target):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        for name in files:
            fp = Path(root) / name
            ok, reason = _file_eligible(fp, config, extensions)
            if ok:
                reviewed.append(fp)
            elif reason:
                skipped.append(f"{fp.relative_to(target)}: {reason}")
    return reviewed, skipped


def os_walk_sorted(root: Path):
    import os

    for root_path, dirnames, filenames in os.walk(root):
        dirnames.sort()
        filenames.sort()
        yield root_path, dirnames, filenames


def _file_eligible(
    path: Path,
    config: ReviewConfig,
    extensions: set[str] | None,
) -> tuple[bool, str | None]:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False, "binary extension"
    try:
        size = path.stat().st_size
    except OSError as e:
        return False, str(e)
    if size > config.max_file_bytes:
        return False, f"exceeds max size ({size} > {config.max_file_bytes})"
    if extensions and path.suffix.lower() not in extensions:
        return False, "extension filter"
    return True, None


def read_snippet(path: Path, start_line: int = 1) -> FileSnippet | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError:
            return None
    return FileSnippet(
        path=str(path),
        language=detect_language(path),
        content=text,
        start_line=start_line,
    )


def git_changed_files(
    repo_root: Path,
    diff_spec: str,
    staged: bool = False,
) -> list[tuple[Path, str]]:
    """Return (absolute path, change_type) for files in diff."""
    repo_root = repo_root.resolve()
    cmd = ["git", "-C", str(repo_root), "diff", "--name-status"]
    if staged:
        cmd.append("--cached")
    elif diff_spec:
        cmd.append(diff_spec)
    else:
        cmd.append("HEAD")
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git diff failed: {e.stderr or e.stdout}") from e
    except FileNotFoundError as e:
        raise RuntimeError("git is not installed or not on PATH") from e

    results: list[tuple[Path, str]] = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, rel = parts
        change = "modified"
        if status.startswith("A"):
            change = "added"
        elif status.startswith("D"):
            change = "deleted"
        elif status.startswith("R"):
            change = "renamed"
            rel = rel.split("\t")[-1] if "\t" in rel else rel
        fp = repo_root / rel
        if change != "deleted" and fp.is_file():
            results.append((fp, change))
    return results


def collect_from_git(
    repo_root: Path,
    config: ReviewConfig,
    diff_spec: str = "",
    staged: bool = False,
    extensions: set[str] | None = None,
) -> tuple[list[FileSnippet], list[str], list[str]]:
    changed = git_changed_files(repo_root, diff_spec, staged=staged)
    snippets: list[FileSnippet] = []
    reviewed: list[str] = []
    skipped: list[str] = []
    for fp, change in changed:
        ok, reason = _file_eligible(fp, config, extensions)
        if not ok:
            skipped.append(f"{fp}: {reason}")
            continue
        sn = read_snippet(fp)
        if not sn:
            skipped.append(f"{fp}: unreadable")
            continue
        sn.change_type = change
        snippets.append(sn)
        reviewed.append(str(fp))
    return snippets, reviewed, skipped


def collect_from_path(
    target: Path,
    config: ReviewConfig,
    extensions: set[str] | None = None,
) -> tuple[list[FileSnippet], list[str], list[str]]:
    paths, skipped = discover_files(target, config, extensions)
    snippets: list[FileSnippet] = []
    reviewed: list[str] = []
    for fp in paths:
        sn = read_snippet(fp)
        if not sn:
            skipped.append(f"{fp}: unreadable")
            continue
        snippets.append(sn)
        reviewed.append(str(fp))
    return snippets, reviewed, skipped