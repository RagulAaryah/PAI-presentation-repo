import pytest

from campus_equipment.data.loan_repository import LoanRepository
from campus_equipment.exceptions import ConflictError, NotFoundError
from campus_equipment.models import Loan


@pytest.fixture
def repo(conn):
    return LoanRepository(conn)


@pytest.fixture
def equipment_id(conn):
    cursor = conn.execute(
        "INSERT INTO equipment (category, description) VALUES ('Laptop', 'Dell XPS 13')"
    )
    conn.commit()
    return cursor.lastrowid


@pytest.fixture
def borrower_id(conn):
    cursor = conn.execute(
        "INSERT INTO borrower (full_name, email, borrower_type) VALUES ('Ada Lovelace', 'ada@warwick.ac.uk', 'student')"
    )
    conn.commit()
    return cursor.lastrowid


def test_add_assigns_id(repo, equipment_id, borrower_id):
    saved = repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-09-01", due_date="2026-09-08")
    )

    assert saved.loan_id is not None
    assert saved.return_date is None


def test_add_with_unknown_equipment_raises_not_found(repo, borrower_id):
    with pytest.raises(NotFoundError):
        repo.add(Loan(equipment_id=999, borrower_id=borrower_id, issue_date="2026-09-01", due_date="2026-09-08"))


def test_add_with_unknown_borrower_raises_not_found(repo, equipment_id):
    with pytest.raises(NotFoundError):
        repo.add(Loan(equipment_id=equipment_id, borrower_id=999, issue_date="2026-09-01", due_date="2026-09-08"))


def test_get_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(999)


def test_find_open_excludes_returned_loans(repo, equipment_id, borrower_id):
    open_loan = repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-09-01", due_date="2026-09-08")
    )
    returned = repo.add(
        Loan(
            equipment_id=equipment_id,
            borrower_id=borrower_id,
            issue_date="2026-08-01",
            due_date="2026-08-08",
            return_date="2026-08-07",
        )
    )

    open_loans = repo.find_open()

    assert [loan.loan_id for loan in open_loans] == [open_loan.loan_id]
    assert returned.loan_id not in [loan.loan_id for loan in open_loans]


def test_find_overdue_excludes_due_today(repo, equipment_id, borrower_id):
    repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-08-20", due_date="2026-09-15")
    )

    overdue = repo.find_overdue(as_of_date="2026-09-15")

    assert overdue == []


def test_find_overdue_includes_loan_due_yesterday(repo, equipment_id, borrower_id):
    saved = repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-08-20", due_date="2026-09-14")
    )

    overdue = repo.find_overdue(as_of_date="2026-09-15")

    assert [loan.loan_id for loan in overdue] == [saved.loan_id]


def test_find_overdue_excludes_returned_loans(repo, equipment_id, borrower_id):
    repo.add(
        Loan(
            equipment_id=equipment_id,
            borrower_id=borrower_id,
            issue_date="2026-08-01",
            due_date="2026-08-08",
            return_date="2026-08-20",
        )
    )

    assert repo.find_overdue(as_of_date="2026-09-15") == []


def test_mark_returned_sets_return_date(repo, equipment_id, borrower_id):
    saved = repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-09-01", due_date="2026-09-08")
    )

    repo.mark_returned(saved.loan_id, return_date="2026-09-05")

    assert repo.get(saved.loan_id).return_date == "2026-09-05"


def test_mark_returned_unknown_loan_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.mark_returned(999, return_date="2026-09-05")


def test_mark_returned_twice_raises_conflict(repo, equipment_id, borrower_id):
    saved = repo.add(
        Loan(equipment_id=equipment_id, borrower_id=borrower_id, issue_date="2026-09-01", due_date="2026-09-08")
    )
    repo.mark_returned(saved.loan_id, return_date="2026-09-05")

    with pytest.raises(ConflictError):
        repo.mark_returned(saved.loan_id, return_date="2026-09-06")
