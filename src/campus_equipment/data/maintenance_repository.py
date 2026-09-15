"""Data access for the maintenance_record table (see
equipment_repository.py for the layer's overall rationale)."""

from __future__ import annotations

import sqlite3

from campus_equipment.exceptions import ConflictError, NotFoundError
from campus_equipment.models import MaintenanceRecord


class MaintenanceRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, record: MaintenanceRecord) -> MaintenanceRecord:
        if self._conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_id = ?", (record.equipment_id,)
        ).fetchone() is None:
            raise NotFoundError(f"No equipment with id {record.equipment_id}")

        cursor = self._conn.execute(
            "INSERT INTO maintenance_record (equipment_id, logged_date, description, resolved_date) "
            "VALUES (?, ?, ?, ?)",
            (record.equipment_id, record.logged_date, record.description, record.resolved_date),
        )
        self._conn.commit()
        record.maintenance_id = cursor.lastrowid
        return record

    def get(self, maintenance_id: int) -> MaintenanceRecord:
        row = self._conn.execute(
            "SELECT * FROM maintenance_record WHERE maintenance_id = ?", (maintenance_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"No maintenance record with id {maintenance_id}")
        return _row_to_record(row)

    def list_all(self) -> list[MaintenanceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM maintenance_record ORDER BY maintenance_id"
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def find_open(self) -> list[MaintenanceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM maintenance_record WHERE resolved_date IS NULL ORDER BY logged_date"
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def find_by_equipment(self, equipment_id: int) -> list[MaintenanceRecord]:
        rows = self._conn.execute(
            "SELECT * FROM maintenance_record WHERE equipment_id = ? ORDER BY logged_date",
            (equipment_id,),
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def mark_resolved(self, maintenance_id: int, resolved_date: str) -> None:
        record = self.get(maintenance_id)
        if record.resolved_date is not None:
            raise ConflictError(
                f"Maintenance record {maintenance_id} was already resolved on {record.resolved_date}"
            )

        self._conn.execute(
            "UPDATE maintenance_record SET resolved_date = ? WHERE maintenance_id = ?",
            (resolved_date, maintenance_id),
        )
        self._conn.commit()


def _row_to_record(row: sqlite3.Row) -> MaintenanceRecord:
    return MaintenanceRecord(
        maintenance_id=row["maintenance_id"],
        equipment_id=row["equipment_id"],
        logged_date=row["logged_date"],
        description=row["description"],
        resolved_date=row["resolved_date"],
    )
