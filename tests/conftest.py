"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, Role, AuditLog
from app.core.security import get_password_hash

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed roles
    roles_data = [
        {"name": "Author", "description": "Can create and edit documents"},
        {"name": "Reviewer", "description": "Can review documents"},
        {"name": "Approver", "description": "Can approve documents"},
        {"name": "DMS_Admin", "description": "Full system administrator"},
    ]
    
    for role_data in roles_data:
        role = Role(**role_data)
        db.add(role)
    
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user for testing"""
    admin_role = db_session.query(Role).filter(Role.name == "DMS_Admin").first()
    
    user = User(
        username="testadmin",
        email="testadmin@test.com",
        hashed_password=get_password_hash("Admin@123"),
        first_name="Test",
        last_name="Admin",
        is_active=True,
    )
    user.roles.append(admin_role)
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Get admin authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "Admin@123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def author_user(db_session):
    """Create an author user for testing"""
    author_role = db_session.query(Role).filter(Role.name == "Author").first()
    
    user = User(
        username="testauthor",
        email="testauthor@test.com",
        hashed_password=get_password_hash("Author@123"),
        first_name="Test",
        last_name="Author",
        is_active=True,
    )
    user.roles.append(author_role)
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def author_token(client, author_user):
    """Get author authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testauthor", "password": "Author@123"}
    )
    return response.json()["access_token"]


