import pytest

from campus_equipment.data.borrower_repository import BorrowerRepository
from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
from campus_equipment.models import Borrower


@pytest.fixture
def repo(conn):
    return BorrowerRepository(conn)


def test_add_assigns_id(repo):
    saved = repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))

    assert saved.borrower_id is not None


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_add_duplicate_email_raises_validation_error(repo):
    repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))

    with pytest.raises(ValidationError):
        repo.add(Borrower(full_name="Ada L.", email="ada@warwick.ac.uk", borrower_type="staff"))


def test_list_all_returns_every_borrower(repo):
    repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    repo.add(Borrower(full_name="Alan Turing", email="alan@warwick.ac.uk", borrower_type="staff"))

    assert len(repo.list_all()) == 2


def test_update_changes_fields(repo):
    saved = repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    saved.phone = "07000000000"

    repo.update(saved)

    assert repo.get(saved.borrower_id).phone == "07000000000"


def test_update_unknown_id_raises_not_found(repo):
    ghost = Borrower(full_name="Ghost", email="ghost@warwick.ac.uk", borrower_type="staff", borrower_id=999)
    with pytest.raises(NotFoundError):
        repo.update(ghost)


def test_delete_removes_borrower(repo):
    saved = repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))

    repo.delete(saved.borrower_id)

    with pytest.raises(NotFoundError):
        repo.get(saved.borrower_id)


def test_delete_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.delete(999)


def test_delete_with_loan_history_is_restricted(repo, conn):
    saved = repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    conn.execute(
        "INSERT INTO equipment (category, description) VALUES ('Laptop', 'Dell XPS 13')"
    )
    conn.execute(
        "INSERT INTO loan (equipment_id, borrower_id, issue_date, due_date) "
        "VALUES (1, ?, '2026-09-01', '2026-09-08')",
        (saved.borrower_id,),
    )
    conn.commit()

    with pytest.raises(ConflictError):
        repo.delete(saved.borrower_id)
