"""Data access for the loan table -- the resolving entity between
equipment and borrower (see equipment_repository.py for the layer's
overall rationale)."""

from __future__ import annotations

import sqlite3

from campus_equipment.exceptions import ConflictError, NotFoundError
from campus_equipment.models import Loan


class LoanRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, loan: Loan) -> Loan:
        if self._conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_id = ?", (loan.equipment_id,)
        ).fetchone() is None:
            raise NotFoundError(f"No equipment with id {loan.equipment_id}")
        if self._conn.execute(
            "SELECT 1 FROM borrower WHERE borrower_id = ?", (loan.borrower_id,)
        ).fetchone() is None:
            raise NotFoundError(f"No borrower with id {loan.borrower_id}")

        try:
            cursor = self._conn.execute(
                "INSERT INTO loan (equipment_id, borrower_id, issue_date, due_date, return_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (loan.equipment_id, loan.borrower_id, loan.issue_date, loan.due_date, loan.return_date),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"Equipment {loan.equipment_id} already has an open loan"
            ) from exc
        loan.loan_id = cursor.lastrowid
        return loan

    def get(self, loan_id: int) -> Loan:
        row = self._conn.execute("SELECT * FROM loan WHERE loan_id = ?", (loan_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"No loan with id {loan_id}")
        return _row_to_loan(row)

    def list_all(self) -> list[Loan]:
        rows = self._conn.execute("SELECT * FROM loan ORDER BY loan_id").fetchall()
        return [_row_to_loan(row) for row in rows]

    def find_open(self) -> list[Loan]:
        rows = self._conn.execute(
            "SELECT * FROM loan WHERE return_date IS NULL ORDER BY due_date"
        ).fetchall()
        return [_row_to_loan(row) for row in rows]

    def find_overdue(self, as_of_date: str) -> list[Loan]:
        rows = self._conn.execute(
            "SELECT * FROM loan WHERE return_date IS NULL AND due_date < ? ORDER BY due_date",
            (as_of_date,),
        ).fetchall()
        return [_row_to_loan(row) for row in rows]

    def mark_returned(self, loan_id: int, return_date: str) -> None:
        loan = self.get(loan_id)
        if loan.return_date is not None:
            raise ConflictError(f"Loan {loan_id} was already returned on {loan.return_date}")

        self._conn.execute(
            "UPDATE loan SET return_date = ? WHERE loan_id = ?", (return_date, loan_id)
        )
        self._conn.commit()


def _row_to_loan(row: sqlite3.Row) -> Loan:
    return Loan(
        loan_id=row["loan_id"],
        equipment_id=row["equipment_id"],
        borrower_id=row["borrower_id"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        return_date=row["return_date"],
    )
