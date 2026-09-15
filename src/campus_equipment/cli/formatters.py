"""Pure display-formatting functions for the CLI.

Kept separate from app.py's input()/print() menu loop specifically so
this formatting logic can be unit tested (see tests/cli/test_formatters.py)
without mocking stdin/stdout.
"""

from __future__ import annotations

from campus_equipment.models import Equipment

_EQUIPMENT_HEADER = f"{'ID':<4}{'Category':<14}{'Description':<28}{'Status':<13}{'Condition':<10}"


def format_equipment_table(items: list[Equipment]) -> str:
    if not items:
        return "No equipment records found."
    lines = [_EQUIPMENT_HEADER, "-" * len(_EQUIPMENT_HEADER)]
    for item in items:
        lines.append(
            f"{item.equipment_id:<4}{item.category:<14}{item.description:<28}{item.status:<13}{item.condition:<10}"
        )
    return "\n".join(lines)


def format_loans_report_table(report: list[dict]) -> str:
    if not report:
        return "No loans found."
    lines = []
    for entry in report:
        parts = [
            f"Loan #{entry['loan_id']}",
            entry["equipment_description"],
            entry["borrower_name"],
            f"due {entry['due_date']}",
        ]
        if "days_overdue" in entry:
            parts.append(f"{entry['days_overdue']} day(s) overdue")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def format_summary(counts: dict[str, int]) -> str:
    return "\n".join(f"{status}: {count}" for status, count in counts.items())
