"""In-memory fakes for the four repositories, implementing the same method
signatures as the real sqlite-backed repositories in campus_equipment.data.

These let the service layer be unit-tested in complete isolation from
SQLite -- fast, and proof that the service layer's only coupling to
persistence is the repository interface, not any particular database
(the architectural goal stated in the brief). They are test support code,
not themselves a TDD'd unit of behaviour -- comparable to conftest.py.
"""

from __future__ import annotations

import copy

from campus_equipment.exceptions import ConflictError, NotFoundError, ValidationError


class FakeEquipmentRepository:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._next_id = 1

    def add(self, equipment):
        equipment = copy.copy(equipment)
        equipment.equipment_id = self._next_id
        self._items[self._next_id] = equipment
        self._next_id += 1
        return copy.copy(equipment)

    def get(self, equipment_id):
        item = self._items.get(equipment_id)
        if item is None:
            raise NotFoundError(f"No equipment with id {equipment_id}")
        return copy.copy(item)

    def list_all(self):
        return [copy.copy(item) for item in self._items.values()]

    def find_by_status(self, status):
        return [copy.copy(item) for item in self._items.values() if item.status == status]

    def update(self, equipment):
        if equipment.equipment_id not in self._items:
            raise NotFoundError(f"No equipment with id {equipment.equipment_id}")
        self._items[equipment.equipment_id] = copy.copy(equipment)

    def delete(self, equipment_id):
        if equipment_id not in self._items:
            raise NotFoundError(f"No equipment with id {equipment_id}")
        del self._items[equipment_id]


class FakeBorrowerRepository:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._next_id = 1

    def add(self, borrower):
        if any(b.email == borrower.email for b in self._items.values()):
            raise ValidationError(f"Email already registered: {borrower.email}")
        borrower = copy.copy(borrower)
        borrower.borrower_id = self._next_id
        self._items[self._next_id] = borrower
        self._next_id += 1
        return copy.copy(borrower)

    def get(self, borrower_id):
        item = self._items.get(borrower_id)
        if item is None:
            raise NotFoundError(f"No borrower with id {borrower_id}")
        return copy.copy(item)

    def list_all(self):
        return [copy.copy(item) for item in self._items.values()]

    def update(self, borrower):
        if borrower.borrower_id not in self._items:
            raise NotFoundError(f"No borrower with id {borrower.borrower_id}")
        self._items[borrower.borrower_id] = copy.copy(borrower)

    def delete(self, borrower_id):
        if borrower_id not in self._items:
            raise NotFoundError(f"No borrower with id {borrower_id}")
        del self._items[borrower_id]


class FakeLoanRepository:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._next_id = 1

    def add(self, loan):
        loan = copy.copy(loan)
        loan.loan_id = self._next_id
        self._items[self._next_id] = loan
        self._next_id += 1
        return copy.copy(loan)

    def get(self, loan_id):
        item = self._items.get(loan_id)
        if item is None:
            raise NotFoundError(f"No loan with id {loan_id}")
        return copy.copy(item)

    def list_all(self):
        return [copy.copy(item) for item in self._items.values()]

    def find_open(self):
        return [copy.copy(i) for i in self._items.values() if i.return_date is None]

    def find_overdue(self, as_of_date):
        return [
            copy.copy(i)
            for i in self._items.values()
            if i.return_date is None and i.due_date < as_of_date
        ]

    def mark_returned(self, loan_id, return_date):
        loan = self.get(loan_id)
        if loan.return_date is not None:
            raise ConflictError(f"Loan {loan_id} was already returned on {loan.return_date}")
        self._items[loan_id].return_date = return_date


class FakeMaintenanceRepository:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._next_id = 1

    def add(self, record):
        record = copy.copy(record)
        record.maintenance_id = self._next_id
        self._items[self._next_id] = record
        self._next_id += 1
        return copy.copy(record)

    def get(self, maintenance_id):
        item = self._items.get(maintenance_id)
        if item is None:
            raise NotFoundError(f"No maintenance record with id {maintenance_id}")
        return copy.copy(item)

    def find_open(self):
        return [copy.copy(i) for i in self._items.values() if i.resolved_date is None]

    def find_by_equipment(self, equipment_id):
        return [copy.copy(i) for i in self._items.values() if i.equipment_id == equipment_id]

    def mark_resolved(self, maintenance_id, resolved_date):
        record = self.get(maintenance_id)
        if record.resolved_date is not None:
            raise ConflictError(
                f"Maintenance record {maintenance_id} was already resolved on {record.resolved_date}"
            )
        self._items[maintenance_id].resolved_date = resolved_date
