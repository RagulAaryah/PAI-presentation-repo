from campus_equipment.cli.formatters import (
    format_equipment_table,
    format_loans_report_table,
    format_summary,
)
from campus_equipment.models import Equipment


def test_format_equipment_table_lists_each_item():
    items = [
        Equipment(equipment_id=1, category="Laptop", description="Dell XPS 13", status="available", condition="good"),
        Equipment(equipment_id=2, category="Camera", description="Canon EOS", status="on_loan", condition="fair"),
    ]

    table = format_equipment_table(items)

    assert "Dell XPS 13" in table
    assert "Canon EOS" in table
    assert "on_loan" in table


def test_format_equipment_table_handles_empty_list():
    assert "No equipment" in format_equipment_table([])


def test_format_loans_report_table_lists_each_entry():
    report = [
        {
            "loan_id": 1,
            "equipment_description": "Dell XPS 13",
            "borrower_name": "Ada Lovelace",
            "due_date": "2026-09-10",
            "days_overdue": 5,
        }
    ]

    table = format_loans_report_table(report)

    assert "Dell XPS 13" in table
    assert "Ada Lovelace" in table
    assert "5" in table


def test_format_loans_report_table_handles_empty_list():
    assert "No loans" in format_loans_report_table([])


def test_format_summary_renders_each_status_count():
    text = format_summary({"available": 2, "on_loan": 1, "maintenance": 1})

    assert "available: 2" in text
    assert "on_loan: 1" in text
    assert "maintenance: 1" in text
