from __future__ import annotations

import re
from pathlib import Path

from app.agents.job_search.tests.regression_metrics import (
    collect_regression_metrics,
    latest_metric_report_lines,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
REPORT_PATH = REPO_ROOT / "jobsearch_report.md"
LATEST_CHANGELOG_TITLE = "Full-Matrix Intent Coverage and Study Material Quality Audit"


def _latest_after_metrics_block(report_text: str) -> str:
    marker = f"## Change Log - 2026-07-02 - {LATEST_CHANGELOG_TITLE}"
    if marker not in report_text:
        raise AssertionError(f"Missing latest changelog section: {LATEST_CHANGELOG_TITLE}")
    section = report_text.split(marker, 1)[1]
    if "### After metrics" not in section:
        raise AssertionError("Latest changelog is missing '### After metrics' block")
    after = section.split("### After metrics", 1)[1]
    after = after.split("### Remaining Issues", 1)[0]
    return after


def _extract_metric_line(block: str, label: str) -> str:
    pattern = rf"^- {re.escape(label)}:\s*(.+)$"
    match = re.search(pattern, block, flags=re.M)
    if not match:
        raise AssertionError(f"Report missing metric line: {label}")
    return match.group(1).strip()


def test_jobsearch_report_matches_latest_metrics() -> None:
    report_text = REPORT_PATH.read_text()
    metrics = collect_regression_metrics()
    expected = latest_metric_report_lines()
    block = _latest_after_metrics_block(report_text)

    assert _extract_metric_line(block, "Recalibrated domain density") == expected["recalibrated_domain_density"]
    assert _extract_metric_line(block, "Core domain term coverage") == expected["core_domain_term_coverage"]
    assert _extract_metric_line(block, "Expert naturalness score average") == expected["expert_naturalness_average"]
    assert _extract_metric_line(block, "Formulaic spoken-label count") == expected["formulaic_spoken_label_count"]
    assert _extract_metric_line(block, "Average answer length") == expected["average_answer_length"]
    assert _extract_metric_line(block, "Golden regression pass rate") == expected["golden_pass_rate"]
    assert _extract_metric_line(block, "Broad-role regression pass rate") == expected["broad_role_pass_rate"]
    assert _extract_metric_line(block, "Study depth score") == expected["study_depth_score"]

    overlap_line = _extract_metric_line(block, "Compliance/workflow paragraph overlap (avg)")
    assert expected["compliance_workflow_overlap_avg"] in overlap_line

    assert "Barista" in report_text
    assert "42.5%" in report_text
    assert "non-blocking low outlier" in report_text.lower()
    assert metrics["non_blocking_low_outliers"], "Expected Barista non-blocking low outlier in metric source"
    assert metrics["blocking_outliers"] == [], f"Unexpected blocking outliers: {metrics['blocking_outliers']}"
