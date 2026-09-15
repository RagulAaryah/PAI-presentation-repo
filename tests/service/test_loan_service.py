import pytest

from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError
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
def available_equipment(equipment_repo):
    return equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13"))


@pytest.fixture
def borrower(borrower_repo):
    return borrower_repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))


def test_issue_loan_success_marks_equipment_on_loan(service, equipment_repo, available_equipment, borrower):
    loan = service.issue_loan(
        equipment_id=available_equipment.equipment_id,
        borrower_id=borrower.borrower_id,
        issue_date="2026-09-15",
        due_date="2026-09-22",
    )

    assert loan.loan_id is not None
    assert loan.return_date is None
    assert equipment_repo.get(available_equipment.equipment_id).status == "on_loan"


def test_issue_loan_rejects_equipment_already_on_loan(service, equipment_repo, available_equipment, borrower):
    available_equipment.status = "on_loan"
    equipment_repo.update(available_equipment)

    with pytest.raises(ConflictError):
        service.issue_loan(
            equipment_id=available_equipment.equipment_id,
            borrower_id=borrower.borrower_id,
            issue_date="2026-09-15",
            due_date="2026-09-22",
        )


def test_issue_loan_rejects_equipment_under_maintenance(service, equipment_repo, available_equipment, borrower):
    available_equipment.status = "maintenance"
    equipment_repo.update(available_equipment)

    with pytest.raises(ConflictError):
        service.issue_loan(
            equipment_id=available_equipment.equipment_id,
            borrower_id=borrower.borrower_id,
            issue_date="2026-09-15",
            due_date="2026-09-22",
        )


def test_issue_loan_unknown_equipment_raises_not_found(service, borrower):
    with pytest.raises(NotFoundError):
        service.issue_loan(
            equipment_id=999,
            borrower_id=borrower.borrower_id,
            issue_date="2026-09-15",
            due_date="2026-09-22",
        )


def test_issue_loan_unknown_borrower_raises_not_found(service, available_equipment):
    with pytest.raises(NotFoundError):
        service.issue_loan(
            equipment_id=available_equipment.equipment_id,
            borrower_id=999,
            issue_date="2026-09-15",
            due_date="2026-09-22",
        )


def test_issue_loan_rejects_due_date_before_issue_date(service, available_equipment, borrower):
    with pytest.raises(ValidationError):
        service.issue_loan(
            equipment_id=available_equipment.equipment_id,
            borrower_id=borrower.borrower_id,
            issue_date="2026-09-15",
            due_date="2026-09-10",
        )
