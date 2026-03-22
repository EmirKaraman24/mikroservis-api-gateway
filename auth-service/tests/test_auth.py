import pytest
from src.services.auth import AuthService

@pytest.fixture
def auth_service():
    # We might mock the db_client later, but for now we just pass None or a mock dict
    return AuthService(db_client={})

def test_register_success(auth_service):
    """Test that a new user can register successfully."""
    result = auth_service.register("testuser", "test@example.com", "securepass123")
    assert result is True

def test_register_duplicate_username(auth_service):
    """Test that registering with an existing username fails."""
    auth_service.register("testuser", "test1@example.com", "securepass123")
    # Doing it again should fail/return False or raise Exception. Expecting False here for simplicity.
    result = auth_service.register("testuser", "test2@example.com", "newpass456")
    assert result is False

def test_login_success(auth_service):
    """Test that a valid user can log in and receive a token."""
    auth_service.register("loginuser", "login@example.com", "mypassword")
    token = auth_service.login("loginuser", "mypassword")
    assert token is not None
    assert isinstance(token, str)

def test_login_invalid_password(auth_service):
    """Test that login fails with an incorrect password."""
    auth_service.register("loginuser2", "login2@example.com", "mypassword")
    token = auth_service.login("loginuser2", "wrongpassword")
    assert token is None

def test_verify_token_valid(auth_service):
    """Test that a valid token correctly decodes/verifies."""
    auth_service.register("tokenuser", "token@example.com", "pass")
    token = auth_service.login("tokenuser", "pass")
    
    is_valid = auth_service.verify_token(token)
    assert is_valid is True

def test_verify_token_invalid(auth_service):
    """Test an invalid or fake token verification."""
    is_valid = auth_service.verify_token("fake.jwt.token")
    assert is_valid is False
