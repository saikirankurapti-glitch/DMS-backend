"""
Database initialization script
Creates all tables and seeds initial data (roles and admin user)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import User, Role, AuditLog
from app.core.security import get_password_hash
from app.config import settings


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def seed_roles(db: Session):
    """Seed initial roles"""
    print("\nSeeding roles...")
    
    roles_data = [
        {
            "name": "Author",
            "description": "Can create, edit, and submit documents for review"
        },
        {
            "name": "Reviewer",
            "description": "Can review documents and provide comments/suggestions"
        },
        {
            "name": "Approver",
            "description": "Can approve or reject documents with e-signature (HOD/QA Manager/Director)"
        },
        {
            "name": "DMS_Admin",
            "description": "Full system administrator with user management and document publishing capabilities"
        },
    ]
    
    created_roles = []
    for role_data in roles_data:
        # Check if role already exists
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            created_roles.append(role_data["name"])
        else:
            print(f"  - Role '{role_data['name']}' already exists, skipping")
    
    if created_roles:
        db.commit()
        print(f"✓ Created roles: {', '.join(created_roles)}")
    else:
        print("✓ All roles already exist")


def seed_admin_user(db: Session):
    """Seed initial admin user"""
    print("\nSeeding admin user...")
    
    # Check if admin user already exists
    existing_admin = db.query(User).filter(
        User.username == settings.FIRST_ADMIN_USERNAME
    ).first()
    
    if existing_admin:
        print(f"✓ Admin user '{settings.FIRST_ADMIN_USERNAME}' already exists")
        return
    
    # Get DMS_Admin role
    admin_role = db.query(Role).filter(Role.name == "DMS_Admin").first()
    if not admin_role:
        print("✗ Error: DMS_Admin role not found. Please seed roles first.")
        return
    
    # Create admin user
    admin_user = User(
        username=settings.FIRST_ADMIN_USERNAME,
        email=settings.FIRST_ADMIN_EMAIL,
        hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
        first_name="System",
        last_name="Administrator",
        department="IT",
        is_active=True,
        is_temp_password=False,
    )
    
    # Assign DMS_Admin role
    admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Create audit log for admin creation
    from app.core.audit import AuditLogger
    AuditLogger.log(
        db=db,
        user_id=None,
        username="SYSTEM",
        action="USER_CREATED",
        entity_type="User",
        entity_id=admin_user.id,
        description=f"Initial admin user '{admin_user.username}' created during database initialization",
        details={
            "username": admin_user.username,
            "email": admin_user.email,
            "roles": ["DMS_Admin"]
        },
    )
    
    print(f"✓ Admin user created successfully")
    print(f"  Username: {settings.FIRST_ADMIN_USERNAME}")
    print(f"  Email: {settings.FIRST_ADMIN_EMAIL}")
    print(f"  Password: {settings.FIRST_ADMIN_PASSWORD}")
    print(f"  ⚠️  IMPORTANT: Change the admin password after first login!")


def init_db():
    """Initialize database with tables and seed data"""
    print("=" * 60)
    print("Pharma DMS - Database Initialization")
    print("=" * 60)
    
    # Create tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed roles
        seed_roles(db)
        
        # Seed admin user
        seed_admin_user(db)
        
        print("\n" + "=" * 60)
        print("✓ Database initialization completed successfully!")
        print("=" * 60)
        print("\nYou can now start the application with:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        print("\nAccess the API documentation at: http://localhost:8000/api/docs")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()


