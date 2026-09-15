import pytest

from campus_equipment.exceptions import NotFoundError, ValidationError
from campus_equipment.service.borrower_service import BorrowerService
from tests.service.fakes import FakeBorrowerRepository


@pytest.fixture
def service():
    return BorrowerService(FakeBorrowerRepository())


def test_register_borrower_succeeds(service):
    borrower = service.register_borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student")

    assert borrower.borrower_id is not None


def test_register_borrower_blank_name_is_rejected(service):
    with pytest.raises(ValidationError):
        service.register_borrower(full_name="  ", email="ada@warwick.ac.uk", borrower_type="student")


def test_register_borrower_invalid_email_is_rejected(service):
    with pytest.raises(ValidationError):
        service.register_borrower(full_name="Ada Lovelace", email="not-an-email", borrower_type="student")


def test_register_borrower_invalid_type_is_rejected(service):
    with pytest.raises(ValidationError):
        service.register_borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="alumnus")


def test_register_borrower_duplicate_email_is_rejected(service):
    service.register_borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student")

    with pytest.raises(ValidationError):
        service.register_borrower(full_name="Ada L.", email="ada@warwick.ac.uk", borrower_type="staff")


def test_get_borrower_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_borrower(999)


def test_list_borrowers_returns_all(service):
    service.register_borrower(full_name="Ada Lovelace", email="ada@warwick.ac.uk", borrower_type="student")
    service.register_borrower(full_name="Alan Turing", email="alan@warwick.ac.uk", borrower_type="staff")

    assert len(service.list_borrowers()) == 2
