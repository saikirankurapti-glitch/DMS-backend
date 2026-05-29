"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


def test_login_success(client, admin_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "Admin@123"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testadmin"
    assert "DMS_Admin" in data["user"]["roles"]


def test_login_invalid_username(client):
    """Test login with invalid username"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "Admin@123"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_invalid_password(client, admin_user):
    """Test login with invalid password"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "WrongPassword"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, admin_token):
    """Test getting current user profile"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testadmin"
    assert "DMS_Admin" in data["roles"]


def test_get_current_user_no_token(client):
    """Test getting current user without token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


