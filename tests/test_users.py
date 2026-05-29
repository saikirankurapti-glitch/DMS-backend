"""
Tests for user management endpoints
"""
import pytest
from fastapi import status


def test_create_user(client, admin_token):
    """Test creating a new user"""
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "Test@123",
            "first_name": "New",
            "last_name": "User",
            "department": "Test",
            "role_ids": [1]
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@test.com"
    assert len(data["roles"]) == 1


def test_create_user_duplicate_username(client, admin_token, author_user):
    """Test creating user with duplicate username"""
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "testauthor",  # Already exists
            "email": "another@test.com",
            "password": "Test@123",
            "first_name": "Test",
            "last_name": "User",
            "role_ids": [1]
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_user_non_admin(client, author_token):
    """Test that non-admin cannot create users"""
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "Test@123",
            "first_name": "New",
            "last_name": "User",
            "role_ids": [1]
        }
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_users(client, admin_token, author_user):
    """Test listing users"""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert data["total"] >= 2  # admin and author


def test_list_users_filter_by_role(client, admin_token, author_user):
    """Test filtering users by role"""
    response = client.get(
        "/api/v1/users?role=Author",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    
    # Check that all returned users have Author role
    for user in data["users"]:
        role_names = [role["name"] for role in user["roles"]]
        assert "Author" in role_names


def test_get_user(client, admin_token, author_user):
    """Test getting user details"""
    response = client.get(
        f"/api/v1/users/{author_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testauthor"


def test_update_user(client, admin_token, author_user):
    """Test updating user information"""
    response = client.put(
        f"/api/v1/users/{author_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Updated",
            "last_name": "Name"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"


def test_deactivate_user(client, admin_token, author_user):
    """Test deactivating a user"""
    response = client.patch(
        f"/api/v1/users/{author_user.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is False


def test_activate_user(client, admin_token, author_user, db_session):
    """Test activating an inactive user"""
    # First deactivate
    author_user.is_active = False
    db_session.commit()
    
    # Then activate
    response = client.patch(
        f"/api/v1/users/{author_user.id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is True


def test_reset_password(client, admin_token, author_user):
    """Test resetting user password"""
    response = client.post(
        f"/api/v1/users/{author_user.id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "new_password": "NewPass@123",
            "force_change": True
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "Password reset successfully" in data["message"]


