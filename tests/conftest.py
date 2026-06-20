from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db():
    db = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = {"cnt": 0}
    cursor.fetchall.return_value = []
    db.execute.return_value = cursor
    db.execute_fetchall.return_value = []
    return db


@pytest.fixture
def mock_get_db(mock_db):
    return mock_db


@pytest.fixture
def mock_db_with_constitution(mock_db):
    cursor = MagicMock()
    cursor.fetchone.return_value = {"cnt": 1}
    cursor.fetchall.return_value = [
        {"id": "p1", "rank": 1, "principle": "Test principle", "description": "Test"}
    ]
    mock_db.execute.return_value = cursor
    mock_db.execute_fetchall.return_value = [
        {"id": "p1", "rank": 1, "principle": "Test principle", "description": "Test"}
    ]
    return mock_db


@pytest.fixture
def mock_get_db_with_constitution(mock_db_with_constitution):
    return mock_db_with_constitution
