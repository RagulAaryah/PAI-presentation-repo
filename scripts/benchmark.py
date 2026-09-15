"""Quantify, rather than assume, the benefit of indexing equipment.status
and loan.due_date -- the two columns the reporting queries
(EquipmentRepository.find_by_status, LoanRepository.find_overdue) filter
on.

Not unit tested -- a standalone measurement script, not application
behaviour, in the same category as seed_data.py.

Populates two identical in-memory databases from the same random seed
(one left as schema.sql defines it, one with db.add_reporting_indexes()
applied) at a volume large enough (20,000 equipment rows, 50,000 loans)
for SQLite's query planner to actually prefer an index over a full
table scan, then times the two reporting queries against each.
"""

from __future__ import annotations

import random
import sqlite3
import time
from datetime import date, timedelta

from campus_equipment import db

N_EQUIPMENT = 20_000
N_BORROWERS = 2_000
N_LOANS = 50_000
REPEATS = 7
SEED = 42

CATEGORIES = ["Laptop", "Tablet", "Camera", "VR Headset", "Projector", "Microphone"]
STATUS_WEIGHTS = (["available"] * 70) + (["on_loan"] * 25) + (["maintenance"] * 5)
CONDITIONS = ["new", "good", "fair", "poor"]


def _seeded_database(with_indexes: bool) -> sqlite3.Connection:
    conn = db.connect(":memory:")
    db.init_schema(conn)
    if with_indexes:
        db.add_reporting_indexes(conn)

    rng = random.Random(SEED)
    today = date.today()

    equipment_rows = [
        (rng.choice(CATEGORIES), f"Item {i}", rng.choice(STATUS_WEIGHTS), rng.choice(CONDITIONS))
        for i in range(N_EQUIPMENT)
    ]
    conn.executemany(
        "INSERT INTO equipment (category, description, status, condition) VALUES (?, ?, ?, ?)",
        equipment_rows,
    )

    borrower_rows = [
        (f"Borrower {i}", f"borrower{i}@warwick.ac.uk", rng.choice(["student", "staff"]), None)
        for i in range(N_BORROWERS)
    ]
    conn.executemany(
        "INSERT INTO borrower (full_name, email, borrower_type, phone) VALUES (?, ?, ?, ?)",
        borrower_rows,
    )

    # At most one OPEN loan (return_date IS NULL) per equipment_id is now
    # enforced by idx_loan_one_open_per_equipment (schema.sql), so open
    # loans can't be assigned to equipment_id fully at random -- there are
    # only N_EQUIPMENT possible open slots. open_pool is a shuffled queue
    # of equipment_ids handed out one-per-open-loan; once it's exhausted,
    # any further loan that "wants" to be open is generated closed instead
    # (any equipment_id is fine for a closed loan, open or not).
    open_pool = list(range(1, N_EQUIPMENT + 1))
    rng.shuffle(open_pool)
    next_open_slot = 0

    loan_rows = []
    for _ in range(N_LOANS):
        issue_offset = rng.randint(-90, 0)
        due_offset = issue_offset + rng.randint(3, 21)
        wants_open = rng.random() >= 0.5

        if wants_open and next_open_slot < len(open_pool):
            equipment_id = open_pool[next_open_slot]
            next_open_slot += 1
            return_date = None
        else:
            equipment_id = rng.randint(1, N_EQUIPMENT)
            return_date = (today + timedelta(days=issue_offset + rng.randint(1, 20))).isoformat()

        loan_rows.append(
            (
                equipment_id,
                rng.randint(1, N_BORROWERS),
                (today + timedelta(days=issue_offset)).isoformat(),
                (today + timedelta(days=due_offset)).isoformat(),
                return_date,
            )
        )
    conn.executemany(
        "INSERT INTO loan (equipment_id, borrower_id, issue_date, due_date, return_date) VALUES (?, ?, ?, ?, ?)",
        loan_rows,
    )
    conn.commit()
    return conn


def _time_query(conn: sqlite3.Connection, sql: str, params: tuple, repeats: int = REPEATS) -> float:
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        conn.execute(sql, params).fetchall()
        timings.append(time.perf_counter() - start)
    return min(timings)  # best-of-N: minimises OS/scheduler noise


def _query_plan(conn: sqlite3.Connection, sql: str, params: tuple) -> str:
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return "; ".join(row[-1] for row in rows)


def _status_selectivity(conn: sqlite3.Connection, status: str) -> float:
    total = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    matching = conn.execute("SELECT COUNT(*) FROM equipment WHERE status = ?", (status,)).fetchone()[0]
    return matching / total


def run() -> None:
    as_of = date.today().isoformat()
    status_sql = "SELECT * FROM equipment WHERE status = ? ORDER BY equipment_id"
    loan_sql = "SELECT * FROM loan WHERE return_date IS NULL AND due_date < ? ORDER BY due_date"

    print(f"Dataset: {N_EQUIPMENT:,} equipment rows, {N_BORROWERS:,} borrowers, {N_LOANS:,} loans "
          f"(seed={SEED}, best-of-{REPEATS} timing)\n")

    results = {}
    for with_indexes in (False, True):
        label = "with reporting indexes" if with_indexes else "without reporting indexes"
        print(f"-- {label} --")
        conn = _seeded_database(with_indexes)

        available_selectivity = _status_selectivity(conn, "available")
        maintenance_selectivity = _status_selectivity(conn, "maintenance")

        available_time = _time_query(conn, status_sql, ("available",))
        maintenance_time = _time_query(conn, status_sql, ("maintenance",))
        loan_time = _time_query(conn, loan_sql, (as_of,))

        print(f"  status='available' ({available_selectivity:.0%} of rows):    {available_time * 1000:8.2f} ms  "
              f"plan: {_query_plan(conn, status_sql, ('available',))}")
        print(f"  status='maintenance' ({maintenance_selectivity:.0%} of rows): {maintenance_time * 1000:8.2f} ms  "
              f"plan: {_query_plan(conn, status_sql, ('maintenance',))}")
        print(f"  find_overdue(as_of={as_of}):           {loan_time * 1000:8.2f} ms  "
              f"plan: {_query_plan(conn, loan_sql, (as_of,))}")

        results[with_indexes] = (available_time, maintenance_time, loan_time)
        conn.close()
        print()

    (plain_available, plain_maintenance, plain_loan) = results[False]
    (idx_available, idx_maintenance, idx_loan) = results[True]

    print("-- Summary (index speedup, >1x means the index helped) --")
    print(f"  equipment.status, low selectivity  ('available',    ~70% of rows): "
          f"{plain_available / idx_available:5.2f}x")
    print(f"  equipment.status, high selectivity ('maintenance',   ~5% of rows): "
          f"{plain_maintenance / idx_maintenance:5.2f}x")
    print(f"  loan.due_date (find_overdue):                                     "
          f"{plain_loan / idx_loan:5.2f}x")
    print(
        "\nInterpretation: an index only pays off when the filter is selective enough that\n"
        "avoiding most of the table beats the extra cost of an index lookup + row fetch by\n"
        "rowid. 'available' matches most rows, so SQLite gains little (or loses slightly) from\n"
        "the index; 'maintenance' matches a small minority, where the index should show a\n"
        "clearer win. This is why the benefit was measured per-query rather than assumed."
    )


if __name__ == "__main__":
    run()
