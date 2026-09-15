"""Business rules for borrower records.

Depends on a repository through its constructor (not a concrete SQLite
class) so it can be unit-tested against the fakes in tests/service/fakes.py
without a live database -- see tests/service/test_borrower_service.py.
"""

from __future__ import annotations

from campus_equipment.exceptions import ValidationError
from campus_equipment.models import BORROWER_TYPES, Borrower


class BorrowerService:
    def __init__(self, borrower_repo):
        self._repo = borrower_repo

    def register_borrower(
        self, full_name: str, email: str, borrower_type: str, phone: str | None = None
    ) -> Borrower:
        full_name = (full_name or "").strip()
        email = (email or "").strip()
        if not full_name:
            raise ValidationError("Borrower full name cannot be blank")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError(f"Invalid email address: '{email}'")
        if borrower_type not in BORROWER_TYPES:
            raise ValidationError(
                f"Invalid borrower_type '{borrower_type}': must be one of {BORROWER_TYPES}"
            )
        return self._repo.add(
            Borrower(full_name=full_name, email=email, borrower_type=borrower_type, phone=phone)
        )

    def get_borrower(self, borrower_id: int) -> Borrower:
        return self._repo.get(borrower_id)

    def list_borrowers(self) -> list[Borrower]:
        return self._repo.list_all()
