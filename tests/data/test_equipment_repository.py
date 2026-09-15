import pytest

from campus_equipment.data.equipment_repository import EquipmentRepository
from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
from campus_equipment.models import Equipment


@pytest.fixture
def repo(conn):
    return EquipmentRepository(conn)


def test_add_assigns_id_and_defaults(repo):
    saved = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))

    assert saved.equipment_id is not None
    assert saved.status == "available"
    assert saved.condition == "good"


def test_add_persists_explicit_status_and_condition(repo):
    saved = repo.add(
        Equipment(category="Camera", description="Canon EOS", status="available", condition="new")
    )

    fetched = repo.get(saved.equipment_id)
    assert fetched.category == "Camera"
    assert fetched.description == "Canon EOS"
    assert fetched.condition == "new"


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_list_all_returns_every_item(repo):
    repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    repo.add(Equipment(category="Tablet", description="iPad 9th gen"))

    items = repo.list_all()

    assert len(items) == 2
    assert {item.category for item in items} == {"Laptop", "Tablet"}


def test_find_by_status_filters(repo):
    available = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    repo.add(Equipment(category="VR Headset", description="Meta Quest 3", status="maintenance"))

    results = repo.find_by_status("available")

    assert [item.equipment_id for item in results] == [available.equipment_id]


def test_update_changes_fields(repo):
    saved = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    saved.condition = "fair"
    saved.status = "maintenance"

    repo.update(saved)

    fetched = repo.get(saved.equipment_id)
    assert fetched.condition == "fair"
    assert fetched.status == "maintenance"


def test_update_unknown_id_raises_not_found(repo):
    ghost = Equipment(category="Laptop", description="Dell XPS 13", equipment_id=999)
    with pytest.raises(NotFoundError):
        repo.update(ghost)


def test_update_rejects_invalid_status(repo):
    saved = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    saved.status = "lost"

    with pytest.raises(ValidationError):
        repo.update(saved)


def test_delete_removes_item(repo):
    saved = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))

    repo.delete(saved.equipment_id)

    with pytest.raises(NotFoundError):
        repo.get(saved.equipment_id)


def test_delete_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.delete(999)


def test_delete_with_open_loan_is_restricted(repo, conn):
    saved = repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    conn.execute(
        "INSERT INTO borrower (full_name, email, borrower_type) VALUES (?, ?, ?)",
        ("Ada Lovelace", "ada@warwick.ac.uk", "student"),
    )
    conn.execute(
        "INSERT INTO loan (equipment_id, borrower_id, issue_date, due_date) "
        "VALUES (?, 1, '2026-09-01', '2026-09-08')",
        (saved.equipment_id,),
    )
    conn.commit()

    with pytest.raises(ConflictError):
        repo.delete(saved.equipment_id)
