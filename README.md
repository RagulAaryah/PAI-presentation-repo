# Campus Equipment Loan and Maintenance System

Individual resit project for WM9QF-15 (Programming for Artificial
Intelligence), University of Warwick — a CLI application for the
Digital Learning Support team to manage equipment, borrowers, loans and
maintenance, replacing a spreadsheet-and-email process.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the three-layer
design and the reasoning behind each constraint.

## Requirements

- Python 3.10+ (developed against 3.13)
- No external runtime dependencies — only the standard library
  (`sqlite3`) is used in the application itself. `pytest` is a dev-only
  dependency for running the test suite.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest -v
```

Every test is isolated: data-access tests get a fresh in-memory SQLite
connection per test (`tests/conftest.py`); service tests use fake
in-memory repositories (`tests/service/fakes.py`) with no database at
all. See `docs/ARCHITECTURE.md` for why the layering makes this
possible, and the commit history for the test-first, red-then-green
sequence each behaviour was built in (`test:` commits are always
followed by the `feat:` commit that turns them green, never the other
way round).

## Seeding a demonstration database

```bash
python scripts/seed_data.py
```

Creates `data/campus_equipment.db` (gitignored) with 11 equipment items
across 6 categories, 5 borrowers, and 5 loans covering: one active loan,
two overdue loans, two completed on time, one item currently under
maintenance, and one resolved maintenance record.

## Running the application

```bash
python -m campus_equipment.cli.app
```

Optionally pass a different database path as the first argument (the
test suite and `scripts/benchmark.py` never touch this file — they use
`:memory:`).

## Benchmarking

```bash
python scripts/benchmark.py
```

Measures `EquipmentRepository.find_by_status` and
`LoanRepository.find_overdue`'s underlying queries, with and without
the two reporting indexes (`equipment.status`, `loan.due_date`), against
a synthetic 20,000-equipment / 50,000-loan dataset. The result is
nuanced rather than a flat "indexing is faster": the index gives a real
~2x speedup on a selective filter (`status='maintenance'`, ~5% of rows)
but is roughly a wash on a low-selectivity one (`status='available'`,
~70% of rows) — see the script's own interpretation output, and
`docs/ARCHITECTURE.md`'s testing-strategy table for where this fits in
the overall design.

## Development method

Strict TDD: for every unit of behaviour, a failing test was written and
committed first (`test:` commit), confirmed to fail for the intended
reason, then the minimum implementation was written and committed
separately (`feat:` commit) once the test passed. `git log --oneline`
reads as an audit trail of this cycle. Infrastructure that is not itself
business behaviour (`schema.sql`, `db.py`, `models.py`,
`exceptions.py`, `tests/conftest.py`, `tests/service/fakes.py`,
`scripts/seed_data.py`, `scripts/benchmark.py`) is called out as such in
its own docstring/commit message rather than presented as TDD'd, since
it is closer to test/operational tooling than tested application logic.

## AI use disclosure

Code in this repository was written with AI assistance (Claude), within
the module's stated policy that AI use is permitted for "writing or
fixing programming code." The design decisions, business rules, and
architecture were directed and reviewed by the author, who is
responsible for explaining and defending them in the assessed
recording.
