from __future__ import annotations

from code_review_harness.models import ReviewReport

SEVERITY_ICON = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
}


def render_markdown(report: ReviewReport) -> str:
    lines = [
        "# Code Review Report",
        "",
        f"**Scope:** {report.scope}",
        f"**Backend:** {report.backend or report.model}",
        f"**Model:** {report.model}",
        f"**Overall risk:** {report.overall_risk}",
        "",
        "## Summary",
        report.summary,
        "",
        "## Findings by severity",
    ]
    counts = report.counts_by_severity()
    if counts:
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in ("critical", "high", "medium", "low", "info"):
            if counts.get(sev):
                lines.append(f"| {sev} | {counts[sev]} |")
    else:
        lines.append("_No findings._")

    by_category: dict[str, list] = {}
    for f in report.findings:
        by_category.setdefault(f.category, []).append(f)

    for cat in ("security", "bug", "quality", "best_practice"):
        items = by_category.get(cat, [])
        if not items:
            continue
        lines.extend(["", f"## {cat.replace('_', ' ').title()}", ""])
        for f in items:
            icon = SEVERITY_ICON.get(f.severity.value, "")
            loc = f"{f.file}:{f.line_start}"
            if f.line_end != f.line_start:
                loc += f"-{f.line_end}"
            lines.extend(
                [
                    f"### {icon} {f.title} (`{f.severity.value}`)",
                    f"**Location:** `{loc}`",
                    "",
                    f.description,
                    "",
                    f"**Recommendation:** {f.recommendation}",
                    "",
                ]
            )

    lines.extend(["## Files reviewed", ""])
    if report.files_reviewed:
        for p in report.files_reviewed:
            lines.append(f"- `{p}`")
    else:
        lines.append("_None_")

    if report.files_skipped:
        lines.extend(["", "## Files / notes skipped", ""])
        for s in report.files_skipped:
            lines.append(f"- {s}")

    if report.usage:
        lines.extend(
            [
                "",
                "## Token usage",
                f"- prompt: {report.usage.get('prompt_tokens', 0)}",
                f"- completion: {report.usage.get('completion_tokens', 0)}",
            ]
        )

    return "\n".join(lines) + "\n"