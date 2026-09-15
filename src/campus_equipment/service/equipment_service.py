"""Business rules for equipment records.

Depends on a repository through its constructor (not a concrete SQLite
class) so it can be unit-tested against the fakes in tests/service/fakes.py
without a live database -- see tests/service/test_equipment_service.py.
"""

from __future__ import annotations

from campus_equipment.exceptions import ValidationError
from campus_equipment.models import EQUIPMENT_CONDITIONS, Equipment


class EquipmentService:
    def __init__(self, equipment_repo):
        self._repo = equipment_repo

    def create_equipment(self, category: str, description: str, condition: str = "good") -> Equipment:
        category = (category or "").strip()
        description = (description or "").strip()
        if not category:
            raise ValidationError("Equipment category cannot be blank")
        if not description:
            raise ValidationError("Equipment description cannot be blank")
        if condition not in EQUIPMENT_CONDITIONS:
            raise ValidationError(
                f"Invalid condition '{condition}': must be one of {EQUIPMENT_CONDITIONS}"
            )
        return self._repo.add(Equipment(category=category, description=description, condition=condition))

    def get_equipment(self, equipment_id: int) -> Equipment:
        return self._repo.get(equipment_id)

    def list_equipment(self) -> list[Equipment]:
        return self._repo.list_all()

    def available_equipment(self) -> list[Equipment]:
        return self._repo.find_by_status("available")

    def update_condition(self, equipment_id: int, condition: str) -> None:
        if condition not in EQUIPMENT_CONDITIONS:
            raise ValidationError(
                f"Invalid condition '{condition}': must be one of {EQUIPMENT_CONDITIONS}"
            )
        equipment = self._repo.get(equipment_id)
        equipment.condition = condition
        self._repo.update(equipment)

    def remove_equipment(self, equipment_id: int) -> None:
        self._repo.delete(equipment_id)
