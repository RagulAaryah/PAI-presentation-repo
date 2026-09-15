"""Data access for the borrower table. See equipment_repository.py for the
rationale behind this layer's narrow responsibility."""

from __future__ import annotations

import sqlite3

from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
from campus_equipment.models import Borrower


class BorrowerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, borrower: Borrower) -> Borrower:
        try:
            cursor = self._conn.execute(
                "INSERT INTO borrower (full_name, email, borrower_type, phone) "
                "VALUES (?, ?, ?, ?)",
                (borrower.full_name, borrower.email, borrower.borrower_type, borrower.phone),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Invalid borrower field value: {exc}") from exc
        borrower.borrower_id = cursor.lastrowid
        return borrower

    def get(self, borrower_id: int) -> Borrower:
        row = self._conn.execute(
            "SELECT * FROM borrower WHERE borrower_id = ?", (borrower_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"No borrower with id {borrower_id}")
        return _row_to_borrower(row)

    def list_all(self) -> list[Borrower]:
        rows = self._conn.execute("SELECT * FROM borrower ORDER BY borrower_id").fetchall()
        return [_row_to_borrower(row) for row in rows]

    def update(self, borrower: Borrower) -> None:
        try:
            cursor = self._conn.execute(
                "UPDATE borrower SET full_name = ?, email = ?, borrower_type = ?, phone = ? "
                "WHERE borrower_id = ?",
                (
                    borrower.full_name,
                    borrower.email,
                    borrower.borrower_type,
                    borrower.phone,
                    borrower.borrower_id,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Invalid borrower field value: {exc}") from exc
        if cursor.rowcount == 0:
            raise NotFoundError(f"No borrower with id {borrower.borrower_id}")

    def delete(self, borrower_id: int) -> None:
        try:
            cursor = self._conn.execute(
                "DELETE FROM borrower WHERE borrower_id = ?", (borrower_id,)
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"Cannot delete borrower {borrower_id}: they still have loans on record"
            ) from exc
        if cursor.rowcount == 0:
            raise NotFoundError(f"No borrower with id {borrower_id}")


def _row_to_borrower(row: sqlite3.Row) -> Borrower:
    return Borrower(
        borrower_id=row["borrower_id"],
        full_name=row["full_name"],
        email=row["email"],
        borrower_type=row["borrower_type"],
        phone=row["phone"],
    )
