import pytest

from campus_equipment.exceptions import ConflictError, NotFoundError
from campus_equipment.models import Borrower, Equipment
from campus_equipment.service.loan_service import LoanService
from tests.service.fakes import FakeBorrowerRepository, FakeEquipmentRepository, FakeLoanRepository


@pytest.fixture
def equipment_repo():
    return FakeEquipmentRepository()


@pytest.fixture
def borrower_repo():
    return FakeBorrowerRepository()


@pytest.fixture
def loan_repo():
    return FakeLoanRepository()


@pytest.fixture
def service(loan_repo, equipment_repo, borrower_repo):
    return LoanService(loan_repo, equipment_repo, borrower_repo)


@pytest.fixture
def open_loan(service, equipment_repo, borrower_repo):
    equipment = equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13"))
    borrower = borrower_repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    return service.issue_loan(
        equipment_id=equipment.equipment_id,
        borrower_id=borrower.borrower_id,
        issue_date="2026-09-01",
        due_date="2026-09-08",
    )


def test_return_loan_sets_return_date_and_frees_equipment(service, equipment_repo, open_loan):
    service.return_loan(open_loan.loan_id, return_date="2026-09-05")

    assert equipment_repo.get(open_loan.equipment_id).status == "available"


def test_return_loan_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.return_loan(999, return_date="2026-09-05")


def test_return_loan_already_returned_raises_conflict(service, open_loan):
    service.return_loan(open_loan.loan_id, return_date="2026-09-05")

    with pytest.raises(ConflictError):
        service.return_loan(open_loan.loan_id, return_date="2026-09-06")


def test_list_open_loans_excludes_returned(service, open_loan):
    service.return_loan(open_loan.loan_id, return_date="2026-09-05")

    assert service.list_open_loans() == []


def test_list_overdue_loans_excludes_due_today(service, open_loan):
    # open_loan is due 2026-09-08; as_of the due date itself, not yet overdue
    assert service.list_overdue_loans(as_of_date="2026-09-08") == []


def test_list_overdue_loans_includes_loan_due_yesterday(service, open_loan):
    overdue = service.list_overdue_loans(as_of_date="2026-09-09")

    assert [loan.loan_id for loan in overdue] == [open_loan.loan_id]
