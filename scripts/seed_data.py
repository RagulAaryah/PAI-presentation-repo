"""Populate data/campus_equipment.db with a small, realistic dataset for
development, manual demonstration and the benchmarking script.

Not unit tested -- this is an operational script (data population), not
application behaviour, so it sits alongside db.py/conftest.py as
infrastructure. It is written against the service layer rather than
raw SQL or the repositories directly, both to dogfood the same API the
CLI uses and to get the same validation/business rules (e.g. issuing a
loan flips equipment to on_loan) applied to the seed data automatically.

Deliberately includes both the happy path and the edge cases the brief
calls out: an active loan, two overdue loans, two loans completed on
time, equipment currently under maintenance, and a resolved maintenance
record -- so the CLI has something to demonstrate the very first time
it's run against this data.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

from campus_equipment import db
from campus_equipment.data.borrower_repository import BorrowerRepository
from campus_equipment.data.equipment_repository import EquipmentRepository
from campus_equipment.data.loan_repository import LoanRepository
from campus_equipment.data.maintenance_repository import MaintenanceRepository
from campus_equipment.service.borrower_service import BorrowerService
from campus_equipment.service.equipment_service import EquipmentService
from campus_equipment.service.loan_service import LoanService
from campus_equipment.service.maintenance_service import MaintenanceService

DB_PATH = os.path.join("data", "campus_equipment.db")


def seed(conn) -> None:
    equipment_repo = EquipmentRepository(conn)
    borrower_repo = BorrowerRepository(conn)
    loan_repo = LoanRepository(conn)
    maintenance_repo = MaintenanceRepository(conn)

    equipment_service = EquipmentService(equipment_repo)
    borrower_service = BorrowerService(borrower_repo)
    loan_service = LoanService(loan_repo, equipment_repo, borrower_repo)
    maintenance_service = MaintenanceService(maintenance_repo, equipment_repo)

    today = date.today()

    def d(offset: int) -> str:
        return (today + timedelta(days=offset)).isoformat()

    equipment = {
        "laptop1": equipment_service.create_equipment("Laptop", "Dell XPS 13", "good"),
        "laptop2": equipment_service.create_equipment("Laptop", "MacBook Pro 14-inch", "new"),
        "laptop3": equipment_service.create_equipment("Laptop", "Lenovo ThinkPad X1", "fair"),
        "tablet1": equipment_service.create_equipment("Tablet", "iPad 9th gen", "good"),
        "tablet2": equipment_service.create_equipment("Tablet", "Samsung Galaxy Tab S8", "good"),
        "camera1": equipment_service.create_equipment("Camera", "Canon EOS 250D", "good"),
        "camera2": equipment_service.create_equipment("Camera", "Sony A6400", "new"),
        "vr1": equipment_service.create_equipment("VR Headset", "Meta Quest 3", "good"),
        "vr2": equipment_service.create_equipment("VR Headset", "HTC Vive Pro", "poor"),
        "projector1": equipment_service.create_equipment("Projector", "Epson EB-2250U", "good"),
        "mic1": equipment_service.create_equipment("Microphone", "Rode NT-USB", "new"),
    }

    borrowers = {
        "ada": borrower_service.register_borrower("Ada Lovelace", "ada.lovelace@warwick.ac.uk", "student", "07000000001"),
        "alan": borrower_service.register_borrower("Alan Turing", "alan.turing@warwick.ac.uk", "staff", "07000000002"),
        "grace": borrower_service.register_borrower("Grace Hopper", "grace.hopper@warwick.ac.uk", "student"),
        "linus": borrower_service.register_borrower("Linus Torvalds", "linus.torvalds@warwick.ac.uk", "student"),
        "margaret": borrower_service.register_borrower("Margaret Hamilton", "margaret.hamilton@warwick.ac.uk", "staff"),
    }

    # Active loan: issued recently, not yet due.
    loan_service.issue_loan(
        equipment["laptop1"].equipment_id, borrowers["ada"].borrower_id,
        issue_date=d(-2), due_date=d(5),
    )

    # Overdue loans: due date has passed, never returned.
    loan_service.issue_loan(
        equipment["tablet1"].equipment_id, borrowers["alan"].borrower_id,
        issue_date=d(-10), due_date=d(-3),
    )
    loan_service.issue_loan(
        equipment["camera1"].equipment_id, borrowers["grace"].borrower_id,
        issue_date=d(-20), due_date=d(-13),
    )

    # Completed loans: returned on time, equipment freed back to available.
    vr_loan = loan_service.issue_loan(
        equipment["vr1"].equipment_id, borrowers["linus"].borrower_id,
        issue_date=d(-30), due_date=d(-23),
    )
    loan_service.return_loan(vr_loan.loan_id, return_date=d(-25))

    mic_loan = loan_service.issue_loan(
        equipment["mic1"].equipment_id, borrowers["margaret"].borrower_id,
        issue_date=d(-15), due_date=d(-8),
    )
    loan_service.return_loan(mic_loan.loan_id, return_date=d(-9))

    # Maintenance: one still open (equipment unavailable), one resolved.
    maintenance_service.log_maintenance(
        equipment["vr2"].equipment_id, "Screen flickering, needs repair", logged_date=d(-4)
    )
    resolved = maintenance_service.log_maintenance(
        equipment["projector1"].equipment_id, "Bulb replaced", logged_date=d(-12)
    )
    maintenance_service.resolve_maintenance(resolved.maintenance_id, resolved_date=d(-11))


def main() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = db.connect(DB_PATH)
    db.init_schema(conn)
    seed(conn)
    conn.close()
    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    main()
