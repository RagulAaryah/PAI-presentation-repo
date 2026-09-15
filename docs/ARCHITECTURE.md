# Architecture

## Layering

Three layers, each depending only on the one below it:

```
Presentation (cli/)  ->  Service (service/)  ->  Data Access (data/)  ->  SQLite
```

- **Data access** (`data/*_repository.py`): one repository class per entity
  (`EquipmentRepository`, `BorrowerRepository`, `LoanRepository`,
  `MaintenanceRepository`). Each repository's only job is translating
  between SQL rows and the dataclasses in `models.py`. Business rules do
  not live here — a repository will let you set any equipment status the
  schema's CHECK constraint allows, because "is this transition allowed"
  is a business question, not a persistence one.
- **Service** (`service/*_service.py`): one class per area of business
  behaviour (`EquipmentService`, `BorrowerService`, `LoanService`,
  `MaintenanceService`, `ReportingService`). This is where the scenario's
  actual rules live — e.g. `LoanService.issue_loan` rejects equipment that
  is `on_loan` or `maintenance` before a row is ever written. Every
  service takes its repository (or repositories) through its constructor
  rather than importing a concrete SQLite class, which is what makes
  `tests/service/*.py` able to test business rules against the fakes in
  `tests/service/fakes.py` with no database involved at all.
- **Presentation** (`cli/app.py`, `cli/formatters.py`): the interactive
  menu. It calls services only — never a repository, never `sqlite3`
  directly (beyond opening the one connection at startup). `formatters.py`
  is split out separately because it is pure (model/dict in, string out)
  and so is the one part of this layer that is unit tested;
  `app.py`'s `input()`/`print()` loop is verified by actually running it.

Why this split, concretely: it is what makes strict TDD practical for a
project with this many rules. Because `LoanService` depends on an
abstract repository interface, `tests/service/test_loan_service.py` can
assert "rejects issuing equipment that's on loan" in a few milliseconds
against an in-memory Python dict, before `EquipmentRepository` or SQLite
enter the picture at all. Every layer's tests run in isolation from the
ones below it, and the data-access layer's own tests
(`tests/data/*.py`) then separately confirm the real SQLite queries and
constraints behave the way the fakes assumed.

## Entities and the schema (see `src/campus_equipment/schema.sql`)

Four tables in 3NF: `equipment`, `borrower`, `loan`, `maintenance_record`.
`loan` is the resolving entity between `equipment` and `borrower`
(issue/due/return dates); `maintenance_record` references `equipment`
only.

Two constraints are deliberately enforced **at the schema level**, not
only in application code:

- `equipment.status CHECK (status IN ('available', 'on_loan', 'maintenance'))`
  — an invalid status can never be written, even by code that bypasses
  the service layer (a bulk import script, a future feature, a bug).
- `FOREIGN KEY ... ON DELETE RESTRICT` on both of `loan`'s foreign keys
  and on `maintenance_record.equipment_id` — a borrower or equipment
  record with loan/maintenance history literally cannot be deleted while
  referenced. `EquipmentRepository.delete`/`BorrowerRepository.delete`
  catch the resulting `sqlite3.IntegrityError` and re-raise it as the
  domain's `ConflictError`, so this constraint is enforced twice
  (schema and, defensively, nowhere else — there is no separate
  application-level "has open loans?" check to fall out of sync with the
  database).

SQLite does not enforce foreign keys by default; `db.connect()` sets
`PRAGMA foreign_keys = ON` on every connection it opens, which is what
makes `ON DELETE RESTRICT` actually restrict anything.

## Exceptions

`exceptions.py` defines a small domain hierarchy (`ValidationError`,
`NotFoundError`, `ConflictError`, all under `DomainError`) that every
layer above `sqlite3` speaks in. Repositories translate
`sqlite3.IntegrityError` into the appropriate one of these; services
raise them directly for business-rule violations; the CLI catches
`DomainError` in one place per menu and prints it. No layer above the
repositories ever needs to know SQLite is the persistence technology.

## Why SQLite

Zero configuration for a single-user CLI tool with no concurrent-write
requirement, file-based (no separate server process to start before a
demo/recording), and the schema uses only standard SQL (`CHECK`,
`FOREIGN KEY ... ON DELETE RESTRICT`, standard types) so moving to
PostgreSQL/MySQL later would not require redesigning the schema — the
only SQLite-specific code is the two `PRAGMA` statements in `db.py`.

## Testing strategy per layer

| Layer | Test file(s) | What's exercised |
|---|---|---|
| Data access | `tests/data/*.py` | Real SQLite, in-memory (`tests/conftest.py`), one connection per test |
| Service | `tests/service/*.py` | Fakes (`tests/service/fakes.py`) — no database |
| Presentation | `tests/cli/test_formatters.py` | Pure formatting functions only |

`app.py`'s menu loop itself has no automated test — an `input()`/`print()`
loop's own logic is "read a line, call a method, print the result",
which the service-layer tests already cover; what's left to verify is
that the wiring works, which was done by actually running the CLI
end-to-end (golden path: add equipment, register borrower, issue loan,
list/report, return loan, log maintenance; and an error path: attempting
to issue equipment under maintenance) rather than by mocking `stdin`.
