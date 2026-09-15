"""Shared pytest fixtures.

`conn` gives every test its own private in-memory SQLite connection with
the schema freshly applied -- tests never share state or touch a file on
disk, so they can run in any order and in parallel.
"""

import pytest

from campus_equipment import db


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    db.init_schema(connection)
    yield connection
    connection.close()
