"""
Database Initialization and Seeding Helper
Handles automatic table creation and initial seed data on startup.
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn.error")


def init_db_and_seed():
    """
    Creates all tables and seeds initial data (roles, admin user) if not exists.
    Safely handles connection and transaction logic.
    """
    logger.info("Initializing database and verifying tables...")
    
    # 1. Import all models to ensure they are registered in the Base metadata
    from app import models
    from app.database import engine, Base, SessionLocal
    
    try:
        # Create all tables if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables verified and created successfully")
    except Exception as table_err:
        logger.error(f"✗ Failed to create database tables: {table_err}")
        raise table_err
        
    db: Session = SessionLocal()
    try:
        # 2. Seed Default Roles
        from app.models.role import Role
        
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
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing_role:
                role = Role(**role_data)
                db.add(role)
                created_roles.append(role_data["name"])
                
        if created_roles:
            db.commit()
            logger.info(f"✓ Created roles: {', '.join(created_roles)}")
        else:
            logger.info("✓ All roles already exist")
            
        # 3. Seed Default Admin User
        from app.models.user import User
        from app.config import settings
        
        existing_admin = db.query(User).filter(
            User.username == settings.FIRST_ADMIN_USERNAME
        ).first()
        
        if existing_admin:
            logger.info(f"✓ Admin user '{settings.FIRST_ADMIN_USERNAME}' already exists")
            return
            
        # Retrieve the newly created or existing DMS_Admin role
        admin_role = db.query(Role).filter(Role.name == "DMS_Admin").first()
        if not admin_role:
            logger.error("✗ Error: DMS_Admin role not found. Skipping admin user seeding.")
            return
            
        from app.core.security import get_password_hash
        
        # Create admin user instance
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
        
        # 4. Create Audit Log for compliance tracking
        try:
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
            logger.info("✓ Seeded audit log for admin user creation")
        except Exception as audit_err:
            logger.warning(f"⚠️ Failed to create audit log for admin user creation: {audit_err}")
            
        logger.info("✓ Admin user seeded successfully")
        logger.info(f"  Username: {settings.FIRST_ADMIN_USERNAME}")
        logger.info(f"  Email: {settings.FIRST_ADMIN_EMAIL}")
        logger.info("  ⚠️  IMPORTANT: Change the admin password after first login!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during database seeding: {e}")
        raise e
    finally:
        db.close()
