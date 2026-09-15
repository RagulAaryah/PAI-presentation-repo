"""Render docs/diagrams/er_diagram.png from src/campus_equipment/schema.sql.

Presentation asset, not application code or behaviour -- not unit
tested, same category as scripts/seed_data.py. Drawn directly with
matplotlib (no system Graphviz available) so the diagram can be
regenerated any time the schema changes rather than hand-edited.
"""

from __future__ import annotations

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

OUT_PATH = os.path.join("docs", "diagrams", "er_diagram.png")

ENTITIES = {
    "equipment": {
        "pos": (1.0, 4.6),
        "pk": "equipment_id",
        "fields": ["category", "description", "status  CHECK IN (available/on_loan/maintenance)", "condition  CHECK IN (new/good/fair/poor)"],
    },
    "borrower": {
        "pos": (11.0, 4.6),
        "pk": "borrower_id",
        "fields": ["full_name", "email  UNIQUE", "borrower_type  CHECK IN (student/staff)", "phone"],
    },
    "loan": {
        "pos": (6.0, 0.9),
        "pk": "loan_id",
        "fields": ["equipment_id  FK -> equipment", "borrower_id  FK -> borrower", "issue_date", "due_date", "return_date  (NULL = still out)"],
    },
    "maintenance_record": {
        "pos": (1.0, 0.9),
        "pk": "maintenance_id",
        "fields": ["equipment_id  FK -> equipment", "logged_date", "description", "resolved_date  (NULL = still open)"],
    },
}

BOX_W, BOX_H = 4.6, 2.9


def _draw_entity(ax, name: str, spec: dict) -> None:
    x, y = spec["pos"]
    box = mpatches.FancyBboxPatch(
        (x, y), BOX_W, BOX_H,
        boxstyle="round,pad=0.05,rounding_size=0.08",
        linewidth=1.6, edgecolor="#2b3a55", facecolor="#eef3fb",
    )
    ax.add_patch(box)
    ax.text(x + BOX_W / 2, y + BOX_H - 0.32, name, ha="center", va="top",
             fontsize=13, fontweight="bold", color="#1a2540")
    ax.plot([x + 0.15, x + BOX_W - 0.15], [y + BOX_H - 0.55, y + BOX_H - 0.55],
             color="#2b3a55", linewidth=1)
    ax.text(x + 0.25, y + BOX_H - 0.82, f"PK  {spec['pk']}", ha="left", va="top",
             fontsize=10.5, fontweight="bold", color="#1a2540")
    line_y = y + BOX_H - 1.12
    for field in spec["fields"]:
        ax.text(x + 0.25, line_y, field, ha="left", va="top", fontsize=9.5, color="#2b3a55")
        line_y -= 0.34


def _elbow(ax, points: list, one_label_pos: tuple, many_label_pos: tuple, many_label: str) -> None:
    """Draw an orthogonal polyline through `points` and place cardinality labels
    at its two ends -- '1' near the parent entity, '0..*' near the child."""
    xs, ys = zip(*points)
    ax.plot(xs, ys, color="#5a6b8c", linewidth=1.4, zorder=1)
    ax.text(*one_label_pos, "1", fontsize=10, color="#5a6b8c", ha="center")
    ax.text(*many_label_pos, many_label, fontsize=8.5, color="#a03030", ha="center", va="top")


def main() -> None:
    fig, ax = plt.subplots(figsize=(15, 8.4), dpi=150)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title(
        "Campus Equipment Loan and Maintenance System -- Entity-Relationship Diagram",
        fontsize=15, fontweight="bold", color="#1a2540", pad=14,
    )

    for name, spec in ENTITIES.items():
        _draw_entity(ax, name, spec)

    # equipment (1) --- (0..*) maintenance_record -- straight vertical, same x-range
    _elbow(
        ax, [(3.3, 4.6), (3.3, 3.8)],
        one_label_pos=(3.65, 4.35), many_label_pos=(3.65, 3.95),
        many_label="0..*",
    )

    # equipment (1) --- (0..*) loan -- elbow: right side of equipment, down into top of loan
    _elbow(
        ax, [(5.6, 6.0), (7.6, 6.0), (7.6, 3.8)],
        one_label_pos=(6.2, 6.25), many_label_pos=(7.85, 4.1),
        many_label="0..*",
    )

    # borrower (1) --- (0..*) loan -- elbow: left side of borrower, down into top of loan
    _elbow(
        ax, [(11.0, 6.0), (9.4, 6.0), (9.4, 3.8)],
        one_label_pos=(10.4, 6.25), many_label_pos=(9.65, 4.1),
        many_label="0..*",
    )

    ax.text(
        8, 0.35,
        "loan is the resolving entity between equipment and borrower (issue/due/return dates).\n"
        "Status/condition/type values and all foreign keys are enforced at the schema level (CHECK, ON DELETE RESTRICT), not only in application code.",
        ha="center", fontsize=9, color="#444444", style="italic",
    )

    plt.tight_layout()
    plt.savefig(OUT_PATH, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
