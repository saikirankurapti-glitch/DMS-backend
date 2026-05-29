"""
Test script to verify audit logging is working
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.audit import AuditLogger
from app.models import User

def test_audit_logs():
    """Create test audit log entries"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Testing Audit Log Creation")
        print("=" * 60)
        
        # Get admin user
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("❌ Admin user not found. Please create admin user first.")
            return
        
        print(f"✓ Found admin user: {admin.username} (ID: {admin.id})")
        print()
        
        # Create test audit logs
        print("Creating test audit logs...")
        
        # Test log 1: System action
        log1 = AuditLogger.log(
            db=db,
            user_id=None,
            username="SYSTEM",
            action="SYSTEM_TEST",
            entity_type="System",
            entity_id=None,
            description="Test audit log entry created by test script",
            details={"test": True, "purpose": "verification"},
            ip_address="127.0.0.1",
            user_agent="Test Script",
        )
        print(f"✓ Created log ID: {log1.id} - {log1.action}")
        
        # Test log 2: User action
        log2 = AuditLogger.log(
            db=db,
            user_id=admin.id,
            username=admin.username,
            action="TEST_ACTION",
            entity_type="User",
            entity_id=admin.id,
            description=f"Test action performed by {admin.username}",
            details={"test": True, "user_id": admin.id},
            ip_address="127.0.0.1",
            user_agent="Test Script",
        )
        print(f"✓ Created log ID: {log2.id} - {log2.action}")
        
        # Test log 3: Using helper method
        log3 = AuditLogger.log_login(
            db=db,
            user_id=admin.id,
            username=admin.username,
            ip_address="127.0.0.1",
            user_agent="Test Script",
        )
        print(f"✓ Created log ID: {log3.id} - {log3.action}")
        
        print()
        print("=" * 60)
        print("✓ Test audit logs created successfully!")
        print("=" * 60)
        
        # Verify by querying
        from app.models import AuditLog
        count = db.query(AuditLog).count()
        print(f"\nTotal audit logs in database: {count}")
        
        # Show recent logs
        print("\nRecent audit logs:")
        recent = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5).all()
        for log in recent:
            print(f"  - [{log.timestamp}] {log.action} by {log.username}: {log.description}")
        
        print("\n" + "=" * 60)
        print("Now check the Audit Logs page in the frontend!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_audit_logs()

