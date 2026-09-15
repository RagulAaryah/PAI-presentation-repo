-- Campus Equipment Loan and Maintenance System
-- Relational schema (3NF). Business-critical constraints are enforced here,
-- at the schema level, not only in application code:
--   * equipment.status is restricted to a known set of states via CHECK
--   * a borrower/equipment record cannot be deleted while a loan or
--     maintenance record references it (ON DELETE RESTRICT)
-- Foreign key enforcement must be turned on per-connection by the caller
-- (PRAGMA foreign_keys = ON) -- SQLite does not enable it by default.

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT NOT NULL,
    description   TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'available'
                  CHECK (status IN ('available', 'on_loan', 'maintenance')),
    condition     TEXT NOT NULL DEFAULT 'good'
                  CHECK (condition IN ('new', 'good', 'fair', 'poor'))
);

CREATE TABLE IF NOT EXISTS borrower (
    borrower_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    borrower_type TEXT NOT NULL
                  CHECK (borrower_type IN ('student', 'staff')),
    phone         TEXT
);

-- Resolving entity between equipment and borrower.
CREATE TABLE IF NOT EXISTS loan (
    loan_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id  INTEGER NOT NULL,
    borrower_id   INTEGER NOT NULL,
    issue_date    TEXT NOT NULL,
    due_date      TEXT NOT NULL,
    return_date   TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (borrower_id) REFERENCES borrower (borrower_id)
        ON DELETE RESTRICT,
    CHECK (due_date >= issue_date),
    CHECK (return_date IS NULL OR return_date >= issue_date)
);

CREATE TABLE IF NOT EXISTS maintenance_record (
    maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER NOT NULL,
    logged_date     TEXT NOT NULL,
    description     TEXT NOT NULL,
    resolved_date   TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment (equipment_id)
        ON DELETE RESTRICT,
    CHECK (resolved_date IS NULL OR resolved_date >= logged_date)
);

-- Note: indexes on equipment.status and loan.due_date are deliberately NOT
-- created here. scripts/benchmark.py adds them via db.add_reporting_indexes()
-- on a copy of the seeded database so the performance benefit of indexing
-- those two reporting-critical columns can be measured, not assumed.
