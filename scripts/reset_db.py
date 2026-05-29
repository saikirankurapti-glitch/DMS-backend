"""
Reset database script
WARNING: This will delete all data and recreate the database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import engine, Base
from scripts.init_db import init_db


def reset_db():
    """Drop all tables and reinitialize database"""
    print("=" * 60)
    print("⚠️  WARNING: Database Reset")
    print("=" * 60)
    print("This will DELETE ALL DATA in the database!")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != "yes":
        print("Database reset cancelled.")
        return
    
    print("\nDropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped")
    
    # Reinitialize
    init_db()


if __name__ == "__main__":
    reset_db()


