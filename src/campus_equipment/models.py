"""Plain dataclasses representing rows of each entity table.

These carry data between layers; they hold no persistence or business
logic themselves (that belongs to the repositories and services
respectively), keeping each class's responsibility narrow.
"""

from __future__ import annotations

from dataclasses import dataclass

EQUIPMENT_STATUSES = ("available", "on_loan", "maintenance")
EQUIPMENT_CONDITIONS = ("new", "good", "fair", "poor")
BORROWER_TYPES = ("student", "staff")


@dataclass
class Equipment:
    category: str
    description: str
    status: str = "available"
    condition: str = "good"
    equipment_id: int | None = None


@dataclass
class Borrower:
    full_name: str
    email: str
    borrower_type: str
    phone: str | None = None
    borrower_id: int | None = None


@dataclass
class Loan:
    equipment_id: int
    borrower_id: int
    issue_date: str
    due_date: str
    return_date: str | None = None
    loan_id: int | None = None


@dataclass
class MaintenanceRecord:
    equipment_id: int
    logged_date: str
    description: str
    resolved_date: str | None = None
    maintenance_id: int | None = None
