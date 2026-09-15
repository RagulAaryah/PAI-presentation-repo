import pytest

from campus_equipment.data.maintenance_repository import MaintenanceRepository
from campus_equipment.exceptions import ConflictError, NotFoundError
from campus_equipment.models import MaintenanceRecord


@pytest.fixture
def repo(conn):
    return MaintenanceRepository(conn)


@pytest.fixture
def equipment_id(conn):
    cursor = conn.execute(
        "INSERT INTO equipment (category, description) VALUES ('VR Headset', 'Meta Quest 3')"
    )
    conn.commit()
    return cursor.lastrowid


def test_add_assigns_id(repo, equipment_id):
    saved = repo.add(
        MaintenanceRecord(equipment_id=equipment_id, logged_date="2026-09-10", description="Cracked lens")
    )

    assert saved.maintenance_id is not None
    assert saved.resolved_date is None


def test_add_with_unknown_equipment_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.add(MaintenanceRecord(equipment_id=999, logged_date="2026-09-10", description="Cracked lens"))


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_find_open_excludes_resolved_records(repo, equipment_id):
    open_record = repo.add(
        MaintenanceRecord(equipment_id=equipment_id, logged_date="2026-09-10", description="Cracked lens")
    )
    repo.add(
        MaintenanceRecord(
            equipment_id=equipment_id,
            logged_date="2026-08-01",
            description="Battery replaced",
            resolved_date="2026-08-03",
        )
    )

    open_records = repo.find_open()

    assert [r.maintenance_id for r in open_records] == [open_record.maintenance_id]


def test_find_by_equipment_returns_full_history(repo, equipment_id):
    repo.add(MaintenanceRecord(equipment_id=equipment_id, logged_date="2026-09-10", description="Cracked lens"))
    repo.add(
        MaintenanceRecord(
            equipment_id=equipment_id,
            logged_date="2026-08-01",
            description="Battery replaced",
            resolved_date="2026-08-03",
        )
    )

    assert len(repo.find_by_equipment(equipment_id)) == 2


def test_mark_resolved_sets_resolved_date(repo, equipment_id):
    saved = repo.add(
        MaintenanceRecord(equipment_id=equipment_id, logged_date="2026-09-10", description="Cracked lens")
    )

    repo.mark_resolved(saved.maintenance_id, resolved_date="2026-09-12")

    assert repo.get(saved.maintenance_id).resolved_date == "2026-09-12"


def test_mark_resolved_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.mark_resolved(999, resolved_date="2026-09-12")


def test_mark_resolved_twice_raises_conflict(repo, equipment_id):
    saved = repo.add(
        MaintenanceRecord(equipment_id=equipment_id, logged_date="2026-09-10", description="Cracked lens")
    )
    repo.mark_resolved(saved.maintenance_id, resolved_date="2026-09-12")

    with pytest.raises(ConflictError):
        repo.mark_resolved(saved.maintenance_id, resolved_date="2026-09-13")
