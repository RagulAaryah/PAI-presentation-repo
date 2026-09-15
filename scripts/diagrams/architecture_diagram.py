"""Render docs/diagrams/architecture_diagram.png -- a layered class/
architecture diagram matching the actual module structure under
src/campus_equipment/.

Presentation asset, not application code or behaviour -- not unit
tested, same category as er_diagram.py.
"""

from __future__ import annotations

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

OUT_PATH = os.path.join("docs", "diagrams", "architecture_diagram.png")

LAYER_COLOR = {
    "presentation": ("#fdf1e7", "#b5651d"),
    "service": ("#eaf3ea", "#2f7a3d"),
    "data": ("#eef3fb", "#2b3a55"),
    "shared": ("#f5f0fa", "#5b3a8c"),
}


def _box(ax, x, y, w, h, title, lines, layer):
    fill, edge = LAYER_COLOR[layer]
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.06",
        linewidth=1.4, edgecolor=edge, facecolor=fill,
    ))
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top",
            fontsize=10.5, fontweight="bold", color=edge)
    ax.plot([x + 0.12, x + w - 0.12], [y + h - 0.46, y + h - 0.46], color=edge, linewidth=0.8)
    ty = y + h - 0.68
    for line in lines:
        ax.text(x + w / 2, ty, line, ha="center", va="top", fontsize=8, color="#333333")
        ty -= 0.26


def _arrow(ax, x1, y1, x2, y2, label=None):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#555555", linewidth=1.3, shrinkA=2, shrinkB=2))
    if label:
        ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2, label, fontsize=7.5, color="#555555", style="italic")


def main() -> None:
    fig, ax = plt.subplots(figsize=(18, 9.5), dpi=150)
    ax.set_xlim(0, 19.3)
    ax.set_ylim(0, 11.5)
    ax.axis("off")
    ax.set_title(
        "Campus Equipment Loan and Maintenance System -- Layered Architecture",
        fontsize=15, fontweight="bold", color="#1a2540", pad=14,
    )

    # Layer band labels
    ax.text(0.3, 10.7, "PRESENTATION", fontsize=9, fontweight="bold", color="#b5651d")
    ax.text(0.3, 7.9, "SERVICE", fontsize=9, fontweight="bold", color="#2f7a3d")
    ax.text(0.3, 4.6, "DATA ACCESS", fontsize=9, fontweight="bold", color="#2b3a55")
    ax.text(0.3, 1.7, "PERSISTENCE", fontsize=9, fontweight="bold", color="#444444")

    # Presentation layer
    _box(ax, 1.6, 9.2, 5.6, 1.7, "cli/app.py", [
        "Services (bag of 5 service instances)",
        "equipment_menu / borrower_menu / loan_menu /",
        "maintenance_menu / reports_menu / main()",
        "-- not unit tested, verified by running it --",
    ], "presentation")
    _box(ax, 8.0, 9.2, 4.2, 1.7, "cli/formatters.py", [
        "format_equipment_table()",
        "format_loans_report_table()",
        "format_summary()",
        "-- pure functions, unit tested --",
    ], "presentation")

    # Service layer
    svc_y = 6.4
    svc_w = 2.85
    services = [
        ("EquipmentService", ["create_equipment", "update_condition", "remove_equipment"]),
        ("BorrowerService", ["register_borrower", "get/list_borrowers"]),
        ("LoanService", ["issue_loan", "return_loan", "list_open/overdue"]),
        ("MaintenanceService", ["log_maintenance", "resolve_maintenance"]),
        ("ReportingService", ["availability_summary", "overdue/current report"]),
    ]
    for i, (name, methods) in enumerate(services):
        _box(ax, 0.6 + i * (svc_w + 0.15), svc_y, svc_w, 1.9, name, methods, "service")

    # Data access layer
    data_y = 3.4
    data_w = 3.5
    repos = [
        ("EquipmentRepository", ["add/get/update/delete", "find_by_status"]),
        ("BorrowerRepository", ["add/get/update/delete"]),
        ("LoanRepository", ["add/get/mark_returned", "find_open/find_overdue"]),
        ("MaintenanceRepository", ["add/get/mark_resolved", "find_open"]),
    ]
    for i, (name, methods) in enumerate(repos):
        _box(ax, 0.9 + i * (data_w + 0.2), data_y, data_w, 1.7, name, methods, "data")

    # Persistence
    _box(ax, 5.3, 0.6, 5.4, 1.4, "SQLite (schema.sql)", [
        "equipment | borrower | loan | maintenance_record",
        "CHECK constraints + FOREIGN KEY ... ON DELETE RESTRICT",
    ], "data")

    # Shared, cross-cutting modules (right column, clear of the main flow)
    ax.text(16.0, 10.7, "SHARED", fontsize=9, fontweight="bold", color="#5b3a8c")
    _box(ax, 16.0, 6.4, 2.9, 1.9, "models.py", [
        "Equipment, Borrower,", "Loan, MaintenanceRecord", "(plain dataclasses)",
    ], "shared")
    _box(ax, 16.0, 3.9, 2.9, 1.9, "exceptions.py", [
        "DomainError", "|- ValidationError", "|- NotFoundError", "|- ConflictError",
    ], "shared")
    _box(ax, 16.0, 1.4, 2.9, 1.9, "db.py", [
        "connect() -- PRAGMA", "foreign_keys = ON", "init_schema()",
        "add_reporting_indexes()",
    ], "shared")

    # Dependency arrows -- presentation -> service -> data -> sqlite
    _arrow(ax, 4.4, 9.15, 3.0, 8.35, "depends on")
    _arrow(ax, 2.3, 6.35, 2.5, 5.15, "constructor-injected repo")
    _arrow(ax, 8.05, 3.35, 8.0, 2.05, "sqlite3.Connection")

    ax.text(
        8, 0.05,
        "Arrows show compile-time dependency direction only (top depends on bottom); each service is unit-tested against a fake\n"
        "implementing the repository's methods (tests/service/fakes.py), so the arrow from service to data access is an interface, not a hard link to SQLite.",
        ha="center", fontsize=8.5, color="#444444", style="italic",
    )

    plt.tight_layout()
    plt.savefig(OUT_PATH, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
