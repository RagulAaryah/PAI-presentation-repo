import pytest

from campus_equipment.exceptions import NotFoundError, ValidationError
from campus_equipment.service.equipment_service import EquipmentService
from tests.service.fakes import FakeEquipmentRepository


@pytest.fixture
def service():
    return EquipmentService(FakeEquipmentRepository())


def test_create_equipment_defaults_to_available(service):
    item = service.create_equipment(category="Laptop", description="Dell XPS 13")

    assert item.status == "available"
    assert item.condition == "good"


def test_create_equipment_blank_category_is_rejected(service):
    with pytest.raises(ValidationError):
        service.create_equipment(category="  ", description="Dell XPS 13")


def test_create_equipment_blank_description_is_rejected(service):
    with pytest.raises(ValidationError):
        service.create_equipment(category="Laptop", description="")


def test_create_equipment_invalid_condition_is_rejected(service):
    with pytest.raises(ValidationError):
        service.create_equipment(category="Laptop", description="Dell XPS 13", condition="broken")


def test_update_condition_changes_stored_value(service):
    item = service.create_equipment(category="Laptop", description="Dell XPS 13")

    service.update_condition(item.equipment_id, "fair")

    assert service.get_equipment(item.equipment_id).condition == "fair"


def test_update_condition_invalid_value_is_rejected(service):
    item = service.create_equipment(category="Laptop", description="Dell XPS 13")

    with pytest.raises(ValidationError):
        service.update_condition(item.equipment_id, "broken")


def test_update_condition_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.update_condition(999, "fair")


def test_available_equipment_filters_by_status(service):
    available = service.create_equipment(category="Laptop", description="Dell XPS 13")
    service.create_equipment(category="VR Headset", description="Meta Quest 3", condition="new")
    unavailable = service.get_equipment(2)
    unavailable.status = "maintenance"
    service._repo.update(unavailable)

    results = service.available_equipment()

    assert [i.equipment_id for i in results] == [available.equipment_id]


def test_remove_equipment_delegates_to_repository(service):
    item = service.create_equipment(category="Laptop", description="Dell XPS 13")

    service.remove_equipment(item.equipment_id)

    with pytest.raises(NotFoundError):
        service.get_equipment(item.equipment_id)
