"""Data access for the equipment table.

Only SQL execution and row<->dataclass mapping live here. Business rules
(e.g. "an item under maintenance cannot be loaned") belong in the service
layer, which depends on this class through its constructor so it can be
substituted with a fake in unit tests -- see service/equipment_service.py.
"""

from __future__ import annotations

import sqlite3

from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
from campus_equipment.models import Equipment


class EquipmentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, equipment: Equipment) -> Equipment:
        cursor = self._conn.execute(
            "INSERT INTO equipment (category, description, status, condition) "
            "VALUES (?, ?, ?, ?)",
            (equipment.category, equipment.description, equipment.status, equipment.condition),
        )
        self._conn.commit()
        equipment.equipment_id = cursor.lastrowid
        return equipment

    def get(self, equipment_id: int) -> Equipment:
        row = self._conn.execute(
            "SELECT * FROM equipment WHERE equipment_id = ?", (equipment_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"No equipment with id {equipment_id}")
        return _row_to_equipment(row)

    def list_all(self) -> list[Equipment]:
        rows = self._conn.execute("SELECT * FROM equipment ORDER BY equipment_id").fetchall()
        return [_row_to_equipment(row) for row in rows]

    def find_by_status(self, status: str) -> list[Equipment]:
        rows = self._conn.execute(
            "SELECT * FROM equipment WHERE status = ? ORDER BY equipment_id", (status,)
        ).fetchall()
        return [_row_to_equipment(row) for row in rows]

    def update(self, equipment: Equipment) -> None:
        try:
            cursor = self._conn.execute(
                "UPDATE equipment SET category = ?, description = ?, status = ?, condition = ? "
                "WHERE equipment_id = ?",
                (
                    equipment.category,
                    equipment.description,
                    equipment.status,
                    equipment.condition,
                    equipment.equipment_id,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Invalid equipment field value: {exc}") from exc
        if cursor.rowcount == 0:
            raise NotFoundError(f"No equipment with id {equipment.equipment_id}")

    def delete(self, equipment_id: int) -> None:
        try:
            cursor = self._conn.execute(
                "DELETE FROM equipment WHERE equipment_id = ?", (equipment_id,)
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                f"Cannot delete equipment {equipment_id}: it is still referenced by a "
                "loan or maintenance record"
            ) from exc
        if cursor.rowcount == 0:
            raise NotFoundError(f"No equipment with id {equipment_id}")


def _row_to_equipment(row: sqlite3.Row) -> Equipment:
    return Equipment(
        equipment_id=row["equipment_id"],
        category=row["category"],
        description=row["description"],
        status=row["status"],
        condition=row["condition"],
    )
