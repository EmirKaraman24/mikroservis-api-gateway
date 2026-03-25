import os
import pytest
from repository import UserRepository
from unittest.mock import MagicMock

@pytest.fixture
def mock_repo():
    repo = UserRepository()
    repo.collection = MagicMock()
    return repo

def test_create_user(mock_repo):
    mock_repo.collection.insert_one.return_value.inserted_id = "12345"
    id = mock_repo.create_user({"name": "Test User", "email": "test@example.com"})
    assert id == "12345"
    mock_repo.collection.insert_one.assert_called_once()

def test_get_user(mock_repo):
    mock_repo.collection.find_one.return_value = {"_id": "12345", "name": "Test User"}
    user = mock_repo.get_user("12345")
    assert user["name"] == "Test User"

def test_update_user(mock_repo):
    mock_repo.update_user("12345", {"name": "Updated User"})
    mock_repo.collection.update_one.assert_called_once()

def test_delete_user(mock_repo):
    mock_repo.delete_user("12345")
    mock_repo.collection.delete_one.assert_called_once()
