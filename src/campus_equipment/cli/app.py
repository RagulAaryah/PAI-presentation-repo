"""Interactive command-line menu -- the presentation layer.

This module is deliberately NOT unit tested: it is a thin input()/print()
loop whose only job is collecting input and calling the service layer
(see cli/formatters.py for the one part of this layer that IS unit
tested, and ARCHITECTURE.md for the rationale). It is verified by
actually running it against the seeded database.

Depends only on the five service classes -- never touches a repository
or sqlite3 directly beyond opening the connection at startup, per the
three-layer architecture in the brief.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from campus_equipment import db
from campus_equipment.data.borrower_repository import BorrowerRepository
from campus_equipment.data.equipment_repository import EquipmentRepository
from campus_equipment.data.loan_repository import LoanRepository
from campus_equipment.data.maintenance_repository import MaintenanceRepository
from campus_equipment.exceptions import DomainError
from campus_equipment.cli.formatters import format_equipment_table, format_loans_report_table, format_summary
from campus_equipment.models import EQUIPMENT_CONDITIONS
from campus_equipment.service.borrower_service import BorrowerService
from campus_equipment.service.equipment_service import EquipmentService
from campus_equipment.service.loan_service import LoanService
from campus_equipment.service.maintenance_service import MaintenanceService
from campus_equipment.service.reporting_service import ReportingService

DEFAULT_DB_PATH = "data/campus_equipment.db"


class Services:
    """Bag of the five service instances the menu functions call into."""

    def __init__(self, conn):
        equipment_repo = EquipmentRepository(conn)
        borrower_repo = BorrowerRepository(conn)
        loan_repo = LoanRepository(conn)
        maintenance_repo = MaintenanceRepository(conn)

        self.equipment = EquipmentService(equipment_repo)
        self.borrower = BorrowerService(borrower_repo)
        self.loan = LoanService(loan_repo, equipment_repo, borrower_repo)
        self.maintenance = MaintenanceService(maintenance_repo, equipment_repo)
        self.reporting = ReportingService(equipment_repo, borrower_repo, loan_repo)


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def _prompt_int(label: str) -> int:
    while True:
        raw = input(f"{label}: ").strip()
        try:
            return int(raw)
        except ValueError:
            print(f"'{raw}' is not a valid number. Please try again.")


def equipment_menu(services: Services) -> None:
    while True:
        print(
            "\n-- Equipment management --\n"
            "1. Add equipment\n2. List all equipment\n3. List available equipment\n"
            "4. Update condition\n5. Remove equipment\n0. Back"
        )
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                category = _prompt("Category")
                description = _prompt("Description")
                condition = _prompt(f"Condition {EQUIPMENT_CONDITIONS}", "good")
                item = services.equipment.create_equipment(category, description, condition)
                print(f"Added equipment #{item.equipment_id}.")
            elif choice == "2":
                print(format_equipment_table(services.equipment.list_equipment()))
            elif choice == "3":
                print(format_equipment_table(services.equipment.available_equipment()))
            elif choice == "4":
                equipment_id = _prompt_int("Equipment ID")
                condition = _prompt(f"New condition {EQUIPMENT_CONDITIONS}")
                services.equipment.update_condition(equipment_id, condition)
                print("Condition updated.")
            elif choice == "5":
                equipment_id = _prompt_int("Equipment ID")
                services.equipment.remove_equipment(equipment_id)
                print("Equipment removed.")
            elif choice == "0":
                return
            else:
                print("Unknown option.")
        except DomainError as exc:
            print(f"Error: {exc}")


def borrower_menu(services: Services) -> None:
    while True:
        print("\n-- Borrower management --\n1. Register borrower\n2. List borrowers\n0. Back")
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                full_name = _prompt("Full name")
                email = _prompt("Email")
                borrower_type = _prompt("Type (student/staff)")
                phone = _prompt("Phone (optional)", "") or None
                borrower = services.borrower.register_borrower(full_name, email, borrower_type, phone)
                print(f"Registered borrower #{borrower.borrower_id}.")
            elif choice == "2":
                for b in services.borrower.list_borrowers():
                    print(f"#{b.borrower_id} {b.full_name} <{b.email}> ({b.borrower_type})")
            elif choice == "0":
                return
            else:
                print("Unknown option.")
        except DomainError as exc:
            print(f"Error: {exc}")


def loan_menu(services: Services) -> None:
    while True:
        print(
            "\n-- Loan processing --\n1. Issue loan\n2. Return loan\n"
            "3. List current loans\n4. List overdue loans\n0. Back"
        )
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                equipment_id = _prompt_int("Equipment ID")
                borrower_id = _prompt_int("Borrower ID")
                issue_date = _prompt("Issue date (YYYY-MM-DD)", date.today().isoformat())
                due_date = _prompt("Due date (YYYY-MM-DD)", (date.today() + timedelta(days=7)).isoformat())
                loan = services.loan.issue_loan(equipment_id, borrower_id, issue_date, due_date)
                print(f"Issued loan #{loan.loan_id}.")
            elif choice == "2":
                loan_id = _prompt_int("Loan ID")
                return_date = _prompt("Return date (YYYY-MM-DD)", date.today().isoformat())
                services.loan.return_loan(loan_id, return_date)
                print("Loan returned.")
            elif choice == "3":
                print(format_loans_report_table(services.reporting.current_loans_report()))
            elif choice == "4":
                as_of = _prompt("As-of date (YYYY-MM-DD)", date.today().isoformat())
                print(format_loans_report_table(services.reporting.overdue_loans_report(as_of)))
            elif choice == "0":
                return
            else:
                print("Unknown option.")
        except DomainError as exc:
            print(f"Error: {exc}")


def maintenance_menu(services: Services) -> None:
    while True:
        print("\n-- Maintenance tracking --\n1. Log maintenance\n2. Resolve maintenance\n0. Back")
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                equipment_id = _prompt_int("Equipment ID")
                description = _prompt("Description of issue")
                logged_date = _prompt("Logged date (YYYY-MM-DD)", date.today().isoformat())
                record = services.maintenance.log_maintenance(equipment_id, description, logged_date)
                print(f"Logged maintenance record #{record.maintenance_id}.")
            elif choice == "2":
                maintenance_id = _prompt_int("Maintenance record ID")
                resolved_date = _prompt("Resolved date (YYYY-MM-DD)", date.today().isoformat())
                services.maintenance.resolve_maintenance(maintenance_id, resolved_date)
                print("Maintenance resolved; equipment is available again.")
            elif choice == "0":
                return
            else:
                print("Unknown option.")
        except DomainError as exc:
            print(f"Error: {exc}")


def reports_menu(services: Services) -> None:
    while True:
        print(
            "\n-- Reports (supervisor view) --\n1. Equipment availability summary\n"
            "2. Overdue loans\n3. Current loans\n0. Back"
        )
        choice = input("Choose an option: ").strip()
        if choice == "1":
            print(format_summary(services.reporting.equipment_availability_summary()))
        elif choice == "2":
            as_of = _prompt("As-of date (YYYY-MM-DD)", date.today().isoformat())
            print(format_loans_report_table(services.reporting.overdue_loans_report(as_of)))
        elif choice == "3":
            print(format_loans_report_table(services.reporting.current_loans_report()))
        elif choice == "0":
            return
        else:
            print("Unknown option.")


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    db_path = argv[0] if argv else DEFAULT_DB_PATH

    conn = db.connect(db_path)
    db.init_schema(conn)
    services = Services(conn)

    print("Campus Equipment Loan and Maintenance System")
    try:
        while True:
            print(
                "\n== Main menu ==\n1. Equipment management\n2. Borrower management\n"
                "3. Loan processing\n4. Maintenance tracking\n5. Reports\n0. Exit"
            )
            choice = input("Choose an option: ").strip()
            if choice == "1":
                equipment_menu(services)
            elif choice == "2":
                borrower_menu(services)
            elif choice == "3":
                loan_menu(services)
            elif choice == "4":
                maintenance_menu(services)
            elif choice == "5":
                reports_menu(services)
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("Unknown option.")
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
