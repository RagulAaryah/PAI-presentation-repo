import pytest

from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
from campus_equipment.models import Equipment
from campus_equipment.service.maintenance_service import MaintenanceService
from tests.service.fakes import FakeEquipmentRepository, FakeMaintenanceRepository


@pytest.fixture
def equipment_repo():
    return FakeEquipmentRepository()


@pytest.fixture
def maintenance_repo():
    return FakeMaintenanceRepository()


@pytest.fixture
def service(maintenance_repo, equipment_repo):
    return MaintenanceService(maintenance_repo, equipment_repo)


@pytest.fixture
def available_equipment(equipment_repo):
    return equipment_repo.add(Equipment(category="VR Headset", description="Meta Quest 3"))


def test_log_maintenance_sets_equipment_status_to_maintenance(service, equipment_repo, available_equipment):
    record = service.log_maintenance(
        equipment_id=available_equipment.equipment_id,
        description="Cracked lens",
        logged_date="2026-09-15",
    )

    assert record.maintenance_id is not None
    assert equipment_repo.get(available_equipment.equipment_id).status == "maintenance"


def test_log_maintenance_rejects_equipment_on_loan(service, equipment_repo, available_equipment):
    available_equipment.status = "on_loan"
    equipment_repo.update(available_equipment)

    with pytest.raises(ConflictError):
        service.log_maintenance(
            equipment_id=available_equipment.equipment_id,
            description="Cracked lens",
            logged_date="2026-09-15",
        )


def test_log_maintenance_unknown_equipment_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.log_maintenance(equipment_id=999, description="Cracked lens", logged_date="2026-09-15")


def test_log_maintenance_blank_description_is_rejected(service, available_equipment):
    with pytest.raises(ValidationError):
        service.log_maintenance(
            equipment_id=available_equipment.equipment_id,
            description="   ",
            logged_date="2026-09-15",
        )
