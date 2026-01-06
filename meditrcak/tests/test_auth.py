"""
Unit tests for authentication routes
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthRoutes:
    """Test cases for authentication endpoints"""

    def test_register_success(self, client, test_db):
        """Test successful user registration"""
        user_data = {
            "full_name": "New User",
            "email": "newuser@example.com",
            "phone": "+1234567890",
            "password": "password123"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["full_name"] == user_data["full_name"]
        assert data["email"] == user_data["email"]
        assert data["phone"] == user_data["phone"]
        assert "id" in data
        assert "role" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails"""
        user_data = {
            "full_name": "Another User",
            "email": test_user.email,  # Same email as existing user
            "phone": "+1234567891",
            "password": "password123"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

    def test_register_invalid_data(self, client):
        """Test registration with invalid data"""
        # Missing required fields
        response = client.post("/auth/register", json={})
        assert response.status_code == 422

        # Invalid email
        response = client.post("/auth/register", json={
            "full_name": "Test User",
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422

    def test_login_success(self, client, test_user):
        """Test successful login"""
        login_data = {
            "username": test_user.email,
            "password": "testpass123"
        }

        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }

        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_invalid_credentials_format(self, client):
        """Test login with invalid credentials format"""
        # Missing password
        response = client.post("/auth/login", data={"username": "test@example.com"})
        assert response.status_code == 422

        # Missing username
        response = client.post("/auth/login", data={"password": "password123"})
        assert response.status_code == 422