from __future__ import annotations

from code_review_harness.models import ReviewFinding, Severity

_SEVERITY_RANK = {
    Severity.CRITICAL: 5,
    Severity.HIGH: 4,
    Severity.MEDIUM: 3,
    Severity.LOW: 2,
    Severity.INFO: 1,
}


def merge_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    by_key: dict[tuple, ReviewFinding] = {}
    for f in findings:
        key = f.dedupe_key()
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = f
            continue
        if _SEVERITY_RANK[f.severity] > _SEVERITY_RANK[existing.severity]:
            by_key[key] = f
    merged = list(by_key.values())
    merged.sort(
        key=lambda x: (
            -_SEVERITY_RANK[x.severity],
            x.file,
            x.line_start,
            x.category,
        )
    )
    return merged


def overall_risk(findings: list[ReviewFinding]) -> str:
    if any(f.severity == Severity.CRITICAL for f in findings):
        return "critical"
    if any(f.severity == Severity.HIGH for f in findings):
        return "high"
    if any(f.severity == Severity.MEDIUM for f in findings):
        return "medium"
    if findings:
        return "low"
    return "none"


def build_summary(findings: list[ReviewFinding], chunk_summaries: list[str]) -> str:
    counts = {s.value: 0 for s in Severity}
    for f in findings:
        counts[f.severity.value] += 1
    parts = [
        f"Found {len(findings)} issue(s): "
        + ", ".join(f"{counts[k]} {k}" for k in counts if counts[k])
    ]
    if findings:
        top = findings[:3]
        parts.append("Top issues: " + "; ".join(f"{t.title} ({t.file}:{t.line_start})" for t in top))
    elif chunk_summaries:
        parts.append("No major issues reported; chunks reviewed successfully.")
    return " ".join(parts)