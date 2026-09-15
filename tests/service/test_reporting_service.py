import pytest

from campus_equipment.models import Borrower, Equipment, Loan
from campus_equipment.service.reporting_service import ReportingService
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
def service(equipment_repo, borrower_repo, loan_repo):
    return ReportingService(equipment_repo, borrower_repo, loan_repo)


def test_equipment_availability_summary_counts_by_status(service, equipment_repo):
    equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13", status="available"))
    equipment_repo.add(Equipment(category="Camera", description="Canon EOS", status="on_loan"))
    equipment_repo.add(Equipment(category="VR Headset", description="Meta Quest 3", status="maintenance"))
    equipment_repo.add(Equipment(category="Tablet", description="iPad 9th gen", status="available"))

    summary = service.equipment_availability_summary()

    assert summary == {"available": 2, "on_loan": 1, "maintenance": 1}


def test_overdue_loans_report_includes_equipment_and_borrower_detail(service, equipment_repo, borrower_repo, loan_repo):
    equipment = equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13", status="on_loan"))
    borrower = borrower_repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    loan_repo.add(
        Loan(equipment_id=equipment.equipment_id, borrower_id=borrower.borrower_id, issue_date="2026-08-20", due_date="2026-09-10")
    )

    report = service.overdue_loans_report(as_of_date="2026-09-15")

    assert len(report) == 1
    entry = report[0]
    assert entry["equipment_description"] == "Dell XPS 13"
    assert entry["borrower_name"] == "Ada Lovelace"
    assert entry["due_date"] == "2026-09-10"
    assert entry["days_overdue"] == 5


def test_overdue_loans_report_excludes_loans_not_yet_due(service, equipment_repo, borrower_repo, loan_repo):
    equipment = equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13", status="on_loan"))
    borrower = borrower_repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    loan_repo.add(
        Loan(equipment_id=equipment.equipment_id, borrower_id=borrower.borrower_id, issue_date="2026-09-10", due_date="2026-09-20")
    )

    assert service.overdue_loans_report(as_of_date="2026-09-15") == []


def test_current_loans_report_lists_open_loans_with_detail(service, equipment_repo, borrower_repo, loan_repo):
    equipment = equipment_repo.add(Equipment(category="Laptop", description="Dell XPS 13", status="on_loan"))
    borrower = borrower_repo.add(Borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student"))
    loan_repo.add(
        Loan(equipment_id=equipment.equipment_id, borrower_id=borrower.borrower_id, issue_date="2026-09-10", due_date="2026-09-20")
    )

    report = service.current_loans_report()

    assert len(report) == 1
    assert report[0]["equipment_description"] == "Dell XPS 13"
    assert report[0]["borrower_name"] == "Ada Lovelace"
