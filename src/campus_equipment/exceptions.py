"""Domain exceptions shared by the service and presentation layers.

Repositories raise these too (translated from sqlite3.IntegrityError,
see data/*.py) so the CLI only ever needs to catch this module's types,
never sqlite3 errors directly -- that would leak the persistence
technology into the presentation layer.
"""


class DomainError(Exception):
    """Base class for all application-defined errors."""


class ValidationError(DomainError):
    """Input failed a business validation rule (bad format, blank field...)."""


class NotFoundError(DomainError):
    """A record referenced by id does not exist."""


class ConflictError(DomainError):
    """The requested operation is blocked by the current state of a record
    (e.g. issuing equipment that is already on loan, deleting equipment
    that still has loans referencing it)."""
