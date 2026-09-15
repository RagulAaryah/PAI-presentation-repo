"""Render docs/diagrams/benchmark_chart.png from a live run of
scripts/benchmark.py -- never hardcoded numbers, so the chart always
reflects an actual measurement on this machine.

Presentation asset, not application code or behaviour -- not unit
tested, same category as the other scripts/diagrams/*.py generators.
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import benchmark as bm  # noqa: E402  (path set up above)

OUT_PATH = os.path.join("docs", "diagrams", "benchmark_chart.png")


def main() -> None:
    as_of = bm.date.today().isoformat()
    status_sql = "SELECT * FROM equipment WHERE status = ? ORDER BY equipment_id"
    loan_sql = "SELECT * FROM loan WHERE return_date IS NULL AND due_date < ? ORDER BY due_date"

    timings = {}
    for with_indexes in (False, True):
        conn = bm._seeded_database(with_indexes)
        timings[with_indexes] = (
            bm._time_query(conn, status_sql, ("available",)) * 1000,
            bm._time_query(conn, status_sql, ("maintenance",)) * 1000,
            bm._time_query(conn, loan_sql, (as_of,)) * 1000,
        )
        conn.close()

    labels = ["status='available'\n(~70% of rows)", "status='maintenance'\n(~5% of rows)", "find_overdue()\n(open + due<today)"]
    without_idx = timings[False]
    with_idx = timings[True]

    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
    x = range(len(labels))
    width = 0.32

    bars_without = ax.bar([i - width / 2 for i in x], without_idx, width, label="Without reporting indexes", color="#c0392b")
    bars_with = ax.bar([i + width / 2 for i in x], with_idx, width, label="With reporting indexes", color="#1f7a4d")

    for bars in (bars_without, bars_with):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f} ms", xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Query time, best-of-7 (ms)")
    ax.set_title(
        f"Index benefit depends on selectivity -- {bm.N_EQUIPMENT:,} equipment rows, {bm.N_LOANS:,} loans",
        fontsize=12.5, fontweight="bold",
    )
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    speedups = [w / i for w, i in zip(without_idx, with_idx)]
    caption = (
        f"Speedup with index: {speedups[0]:.2f}x (available) | "
        f"{speedups[1]:.2f}x (maintenance) | {speedups[2]:.2f}x (overdue loans)\n"
        "A selective filter (maintenance, ~5% of rows) benefits clearly; a low-selectivity filter (available, ~70%) does not -- "
        "measured, not assumed."
    )
    fig.text(0.5, -0.02, caption, ha="center", fontsize=9.5, style="italic", color="#333333")

    plt.tight_layout()
    plt.savefig(OUT_PATH, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT_PATH}")
    print(caption)


if __name__ == "__main__":
    main()
