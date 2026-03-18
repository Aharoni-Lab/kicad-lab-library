"""Markdown report generation for validation results."""
from __future__ import annotations

from typing import Dict, List

from validator.checks import CheckResult


def generate_report(results: Dict[str, CheckResult]) -> str:
    """Format *results* as a Markdown report.

    Parameters
    ----------
    results:
        Mapping of check name / filename to its :class:`CheckResult`.
    """
    all_passed = all(r.passed for r in results.values())
    lines: List[str] = []

    if all_passed:
        lines.append("# Validation Report: PASS")
    else:
        lines.append("# Validation Report: FAIL")

    lines.append("")

    for name, result in results.items():
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"## {name}: {status}")
        if result.errors:
            lines.append("")
            for err in result.errors:
                lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines)
