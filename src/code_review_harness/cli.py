from __future__ import annotations

import argparse
import sys
from pathlib import Path

from code_review_harness.config import validate_config
from code_review_harness.models import Severity
from code_review_harness.orchestrator import default_progress, run_review
from code_review_harness.progress import StatusReporter
from code_review_harness.report import render_json, render_markdown, should_fail_ci


def _parse_extensions(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    exts = set()
    for part in raw.split(","):
        p = part.strip().lower()
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        exts.add(p)
    return exts or None


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="code-review",
        description="LLM code review harness (local Ollama or remote OpenRouter).",
    )
    p.add_argument(
        "target",
        nargs="?",
        default=".",
        help="File or directory to review (default: current directory)",
    )
    p.add_argument(
        "--provider",
        choices=("local", "remote", "ollama", "openrouter"),
        help="Override LLM_PROVIDER from .env (local=Ollama, remote=OpenRouter)",
    )
    p.add_argument(
        "--git",
        action="store_true",
        help="Review files changed in a git repo (target = repo root)",
    )
    p.add_argument(
        "--staged",
        action="store_true",
        help="With --git, only staged changes (--cached)",
    )
    p.add_argument(
        "--diff",
        dest="diff_spec",
        default="",
        metavar="SPEC",
        help="With --git, diff range (e.g. main...HEAD)",
    )
    p.add_argument(
        "--passes",
        default="unified",
        help="Comma-separated: unified, security, bugs, quality, best_practices, or all",
    )
    p.add_argument(
        "--format",
        choices=("md", "json", "both"),
        default="md",
        help="Output format",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write report to file (md/json/both use _report.md or .json suffix if needed)",
    )
    p.add_argument(
        "--ext",
        dest="extensions",
        help="Comma-separated file extensions to include (e.g. py,ts)",
    )
    p.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Cap number of chunks (useful for large repos)",
    )
    p.add_argument(
        "--fail-on",
        choices=[s.value for s in Severity],
        help="Exit code 1 if any finding meets this severity or higher",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress on stderr",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status = StatusReporter(quiet=args.quiet)

    provider_override = None
    if args.provider:
        provider_override = "local" if args.provider in ("local", "ollama") else "remote"

    try:
        config = validate_config(provider_override=provider_override)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    status.configuration_loaded(
        config.provider.value,
        config.model,
        config.base_url,
    )

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Target not found: {target}", file=sys.stderr)
        return 2

    pass_names = [p.strip() for p in args.passes.split(",") if p.strip()]
    progress = None if args.quiet else default_progress

    try:
        report = run_review(
            target=target,
            config=config,
            pass_names=pass_names,
            use_git=args.git or args.staged or bool(args.diff_spec),
            diff_spec=args.diff_spec,
            staged=args.staged,
            extensions=_parse_extensions(args.extensions),
            max_chunks=args.max_chunks,
            on_progress=progress,
            status=status,
        )
    except (RuntimeError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1

    status.generating_report()
    md = render_markdown(report)
    js = render_json(report)

    if args.format in ("md", "both"):
        if args.output and args.format == "md":
            out = args.output if args.output.suffix == ".md" else args.output.with_suffix(".md")
            status.writing_report(str(out))
            _write_output(out, md)
            if not args.quiet:
                print(f"Wrote {out}", file=sys.stderr)
        else:
            print(md, end="" if md.endswith("\n") else "\n")

    if args.format in ("json", "both"):
        if args.output and args.format == "json":
            out = args.output if args.output.suffix == ".json" else args.output.with_suffix(".json")
            status.writing_report(str(out))
            _write_output(out, js)
            if not args.quiet:
                print(f"Wrote {out}", file=sys.stderr)
        elif args.format == "json":
            print(js, end="" if js.endswith("\n") else "\n")
        elif args.output and args.format == "both":
            base = args.output
            md_path = base if str(base).endswith(".md") else base.with_name(base.stem + "_report.md")
            json_path = (
                base.with_suffix(".json")
                if base.suffix == ".md"
                else base.with_name(base.stem + "_report.json")
            )
            status.writing_report(f"{md_path} and {json_path}")
            _write_output(md_path, md)
            _write_output(json_path, js)
            if not args.quiet:
                print(f"Wrote {md_path} and {json_path}", file=sys.stderr)

    if args.fail_on:
        sev = Severity(args.fail_on)
        if should_fail_ci(report, sev):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())