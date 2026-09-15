"""Business rules for issuing and returning loans -- the operation the
scenario's core constraint applies to ("must prevent issuing an item
that's already on loan or unavailable").

Depends on three repositories through its constructor (not concrete
SQLite classes) so it can be unit-tested against the fakes in
tests/service/fakes.py without a live database.
"""

from __future__ import annotations

from campus_equipment.exceptions import ConflictError, ValidationError
from campus_equipment.models import Loan


class LoanService:
    def __init__(self, loan_repo, equipment_repo, borrower_repo):
        self._loans = loan_repo
        self._equipment = equipment_repo
        self._borrowers = borrower_repo

    def issue_loan(self, equipment_id: int, borrower_id: int, issue_date: str, due_date: str) -> Loan:
        equipment = self._equipment.get(equipment_id)
        if equipment.status != "available":
            raise ConflictError(
                f"Equipment {equipment_id} cannot be issued: current status is '{equipment.status}'"
            )
        self._borrowers.get(borrower_id)  # raises NotFoundError if the borrower doesn't exist

        if due_date < issue_date:
            raise ValidationError(
                f"due_date '{due_date}' cannot be before issue_date '{issue_date}'"
            )

        loan = self._loans.add(
            Loan(
                equipment_id=equipment_id,
                borrower_id=borrower_id,
                issue_date=issue_date,
                due_date=due_date,
            )
        )
        equipment.status = "on_loan"
        self._equipment.update(equipment)
        return loan
