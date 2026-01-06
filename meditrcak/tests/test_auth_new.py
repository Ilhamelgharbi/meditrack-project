import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database.db import get_db
from app.auth.models import Base

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Test data
test_user_data = {
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "password": "securepassword123",
    "role": "patient"
}

test_admin_data = {
    "full_name": "Admin User",
    "email": "admin@example.com",
    "phone": "+0987654321",
    "password": "adminpassword123",
    "role": "admin"
}


class TestAuthentication:
    """Test suite for authentication endpoints."""
    
    def test_register_patient_success(self):
        """Test successful patient registration."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["phone"] == test_user_data["phone"]
        assert data["role"] == "patient"
        assert "id" in data
        assert "date_created" in data
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_register_admin_success(self):
        """Test successful admin registration."""
        response = client.post("/auth/register", json=test_admin_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_admin_data["email"]
        assert data["role"] == "admin"
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Register first user
        client.post("/auth/register", json=test_user_data)
        
        # Try to register with same email
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
    
    def test_register_short_password(self):
        """Test registration with password too short."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "newuser@example.com"
        invalid_data["password"] = "12345"
        
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
    
    def test_login_success(self):
        """Test successful login."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login with form data (OAuth2PasswordRequestForm format)
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_get_me_success(self):
        """Test getting current user information."""
        # Register user
        client.post("/auth/register", json=test_user_data)
        
        # Login to get token
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == "patient"
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_get_me_without_token(self):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "could not validate" in response.json()["detail"].lower()
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow: register -> login -> get user info."""
        # Use unique test data to avoid conflicts with other tests
        unique_user_data = {
            "full_name": "Test Flow User",
            "email": "test.flow@example.com",
            "phone": "+1234567890",
            "password": "securepassword123",
            "role": "patient"
        }
        
        # 1. Register
        register_response = client.post("/auth/register", json=unique_user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_data = {
            "username": unique_user_data["email"],
            "password": unique_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Get user info
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert user_data["email"] == unique_user_data["email"]
        assert user_data["full_name"] == unique_user_data["full_name"]
        assert user_data["role"] == "patient"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])