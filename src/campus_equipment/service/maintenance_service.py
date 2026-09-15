"""Business rules for logging and resolving maintenance activity -- the
scenario's other core constraint ("must prevent equipment marked as
under maintenance from being loaned").

Depends on two repositories through its constructor (not concrete
SQLite classes) so it can be unit-tested against the fakes in
tests/service/fakes.py without a live database.
"""

from __future__ import annotations

from campus_equipment.exceptions import ConflictError, ValidationError
from campus_equipment.models import MaintenanceRecord


class MaintenanceService:
    def __init__(self, maintenance_repo, equipment_repo):
        self._maintenance = maintenance_repo
        self._equipment = equipment_repo

    def log_maintenance(self, equipment_id: int, description: str, logged_date: str) -> MaintenanceRecord:
        equipment = self._equipment.get(equipment_id)  # raises NotFoundError if unknown
        if equipment.status == "on_loan":
            raise ConflictError(
                f"Equipment {equipment_id} cannot be sent for maintenance while on loan"
            )

        description = (description or "").strip()
        if not description:
            raise ValidationError("Maintenance description cannot be blank")

        record = self._maintenance.add(
            MaintenanceRecord(equipment_id=equipment_id, logged_date=logged_date, description=description)
        )
        equipment.status = "maintenance"
        self._equipment.update(equipment)
        return record

    def resolve_maintenance(self, maintenance_id: int, resolved_date: str) -> None:
        record = self._maintenance.get(maintenance_id)  # raises NotFoundError if unknown
        self._maintenance.mark_resolved(maintenance_id, resolved_date)  # raises ConflictError if already resolved

        equipment = self._equipment.get(record.equipment_id)
        equipment.status = "available"
        self._equipment.update(equipment)

    def list_open_maintenance(self) -> list[MaintenanceRecord]:
        return self._maintenance.find_open()
