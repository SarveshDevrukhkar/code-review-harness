from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from code_review_harness.models import ReviewReport, ReviewFinding, Severity


def finding_to_dict(f: ReviewFinding) -> dict[str, Any]:
    d = asdict(f)
    d["severity"] = f.severity.value
    return d


def report_to_dict(report: ReviewReport) -> dict[str, Any]:
    return {
        "scope": report.scope,
        "summary": report.summary,
        "overall_risk": report.overall_risk,
        "backend": report.backend or report.model,
        "model": report.model,
        "findings": [finding_to_dict(f) for f in report.findings],
        "files_reviewed": report.files_reviewed,
        "files_skipped": report.files_skipped,
        "counts_by_severity": report.counts_by_severity(),
        "usage": report.usage,
    }


def render_json(report: ReviewReport, indent: int = 2) -> str:
    return json.dumps(report_to_dict(report), indent=indent) + "\n"


def should_fail_ci(report: ReviewReport, fail_on: Severity) -> bool:
    rank = {
        Severity.CRITICAL: 5,
        Severity.HIGH: 4,
        Severity.MEDIUM: 3,
        Severity.LOW: 2,
        Severity.INFO: 1,
    }
    threshold = rank[fail_on]
    return any(rank[f.severity] >= threshold for f in report.findings)