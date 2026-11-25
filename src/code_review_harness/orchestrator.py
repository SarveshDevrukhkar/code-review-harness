from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from code_review_harness.chunking import expand_and_prioritize
from code_review_harness.clients.factory import get_client
from code_review_harness.collector import collect_from_git, collect_from_path
from code_review_harness.merge import build_summary, merge_findings, overall_risk
from code_review_harness.models import ReviewConfig, ReviewReport
from code_review_harness.passes.registry import resolve_passes
from code_review_harness.progress import StatusReporter


def run_review(
    *,
    target: Path,
    config: ReviewConfig,
    pass_names: list[str] | None,
    use_git: bool = False,
    diff_spec: str = "",
    staged: bool = False,
    extensions: set[str] | None = None,
    max_chunks: int | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
    status: StatusReporter | None = None,
) -> ReviewReport:
    scope = _describe_scope(target, use_git, diff_spec, staged)

    if status:
        status.collecting_files()

    if use_git:
        snippets, reviewed, skipped = collect_from_git(
            target, config, diff_spec=diff_spec, staged=staged, extensions=extensions
        )
    else:
        snippets, reviewed, skipped = collect_from_path(target, config, extensions)

    chunks = expand_and_prioritize(snippets, config)
    if max_chunks is not None and len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        skipped.append(f"(truncated to {max_chunks} chunks for this run)")

    passes = resolve_passes(pass_names)

    if status:
        status.chunking(len(chunks), len(passes))

    client = get_client(config)
    repo_context = f"root={target.resolve()}"

    all_findings = []
    summaries: list[str] = []
    backend = client.provider_name

    for i, chunk in enumerate(chunks):
        if on_progress:
            on_progress(i + 1, len(chunks), chunk.path)
        for review_pass in passes:
            if status:
                status.llm_calling(i + 1, len(chunks), review_pass.name, backend)
                status.llm_generating()
            findings, summary = review_pass.run(client, chunk, repo_context)
            if status:
                status.llm_done(len(findings))
            all_findings.extend(findings)
            if summary:
                summaries.append(summary)

    if status:
        status.merging_findings()

    merged = merge_findings(all_findings)
    report = ReviewReport(
        scope=scope,
        summary=build_summary(merged, summaries),
        overall_risk=overall_risk(merged),
        findings=merged,
        files_reviewed=sorted(set(reviewed)),
        files_skipped=skipped,
        model=config.backend_display,
        backend=config.backend_display,
        usage=client.usage,
    )
    return report


def _describe_scope(
    target: Path,
    use_git: bool,
    diff_spec: str,
    staged: bool,
) -> str:
    if use_git:
        if staged:
            return f"git staged diff @ {target}"
        if diff_spec:
            return f"git diff {diff_spec} @ {target}"
        return f"git working tree @ {target}"
    return f"path {target.resolve()}"


def default_progress(current: int, total: int, path: str) -> None:
    print(f"      → Reviewing file [{current}/{total}]: {path}", file=sys.stderr)