"""Cross-cutting summary views for the team supervisor role ("needs
summary information such as overdue loans and equipment currently
unavailable"). Deliberately separate from LoanService/EquipmentService:
these reports compose data from more than one entity and are read-only,
whereas the other services each own one entity's write-path business
rules. Returns plain dicts (a small reporting DTO) rather than raw
model objects so the presentation layer never needs its own repository
access to resolve a loan's equipment/borrower names.
"""

from __future__ import annotations

from datetime import date

from campus_equipment.models import EQUIPMENT_STATUSES


class ReportingService:
    def __init__(self, equipment_repo, borrower_repo, loan_repo):
        self._equipment = equipment_repo
        self._borrowers = borrower_repo
        self._loans = loan_repo

    def equipment_availability_summary(self) -> dict[str, int]:
        summary = {status: 0 for status in EQUIPMENT_STATUSES}
        for item in self._equipment.list_all():
            summary[item.status] += 1
        return summary

    def overdue_loans_report(self, as_of_date: str) -> list[dict]:
        as_of = date.fromisoformat(as_of_date)
        report = []
        for loan in self._loans.find_overdue(as_of_date):
            equipment = self._equipment.get(loan.equipment_id)
            borrower = self._borrowers.get(loan.borrower_id)
            report.append(
                {
                    "loan_id": loan.loan_id,
                    "equipment_description": equipment.description,
                    "borrower_name": borrower.full_name,
                    "due_date": loan.due_date,
                    "days_overdue": (as_of - date.fromisoformat(loan.due_date)).days,
                }
            )
        return report

    def current_loans_report(self) -> list[dict]:
        report = []
        for loan in self._loans.find_open():
            equipment = self._equipment.get(loan.equipment_id)
            borrower = self._borrowers.get(loan.borrower_id)
            report.append(
                {
                    "loan_id": loan.loan_id,
                    "equipment_description": equipment.description,
                    "borrower_name": borrower.full_name,
                    "issue_date": loan.issue_date,
                    "due_date": loan.due_date,
                }
            )
        return report
