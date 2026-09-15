import pytest

from campus_equipment.exceptions import ConflictError, NotFoundError
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
def open_record(service, equipment_repo):
    equipment = equipment_repo.add(Equipment(category="VR Headset", description="Meta Quest 3"))
    return service.log_maintenance(equipment_id=equipment.equipment_id, description="Cracked lens", logged_date="2026-09-15")


def test_resolve_maintenance_sets_equipment_available(service, equipment_repo, open_record):
    service.resolve_maintenance(open_record.maintenance_id, resolved_date="2026-09-17")

    assert equipment_repo.get(open_record.equipment_id).status == "available"


def test_resolve_maintenance_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.resolve_maintenance(999, resolved_date="2026-09-17")


def test_resolve_maintenance_already_resolved_raises_conflict(service, open_record):
    service.resolve_maintenance(open_record.maintenance_id, resolved_date="2026-09-17")

    with pytest.raises(ConflictError):
        service.resolve_maintenance(open_record.maintenance_id, resolved_date="2026-09-18")


def test_list_open_maintenance_excludes_resolved(service, open_record):
    service.resolve_maintenance(open_record.maintenance_id, resolved_date="2026-09-17")

    assert service.list_open_maintenance() == []


def test_list_open_maintenance_includes_unresolved(service, open_record):
    open_records = service.list_open_maintenance()

    assert [r.maintenance_id for r in open_records] == [open_record.maintenance_id]
