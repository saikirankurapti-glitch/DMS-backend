# Database Migration Guide - Q-Docs System

Complete guide for migrating data into, out of, and between Q-Docs databases. Covers full data migrations, partial migrations, and data synchronization scenarios.

---

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Migration Scenarios](#migration-scenarios)
4. [Exporting Data from Source System](#exporting-data-from-source-system)
5. [Importing Data to Q-Docs](#importing-data-to-q-docs)
6. [Data Validation](#data-validation)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting Migration Issues](#troubleshooting-migration-issues)
9. [Post-Migration Verification](#post-migration-verification)

---

## Migration Overview

### Supported Migration Types

| Type | Source | Target | Use Case |
|------|--------|--------|----------|
| **Full Fresh** | Empty | Q-Docs | New deployment, greenfield project |
| **Data Import** | CSV/JSON | Q-Docs | Bulk document/user loading |
| **Legacy System Migration** | Old DMS | Q-Docs | System replacement, consolidation |
| **Database Backup Restore** | Q-Docs Backup | Q-Docs | Disaster recovery, restore point |
| **Incremental Sync** | Source | Q-Docs | Continuous data synchronization |
| **Dev to Production** | PostgreSQL Dev | PostgreSQL Prod | Promotion, zero-downtime deployment |

### Data Migration Architecture

```
┌─────────────────┐
│  Source System  │
│  (Your Old DB)  │
└────────┬────────┘
         │
         │ Export Data
         │ (CSV, JSON, SQL)
         ▼
┌─────────────────────────────┐
│  Data Transformation Layer   │
│  (Validation, Mapping,      │
│   Data Cleansing)           │
└────────┬────────────────────┘
         │
         │ Import Data
         │ (SQL Scripts, API, Bulk)
         ▼
┌─────────────────┐
│    Q-Docs DB    │
│  (PostgreSQL)   │
└─────────────────┘
```

---

## Pre-Migration Checklist

Before starting any migration, verify:

**Planning:**
- [ ] Migration scope defined (which data, which users)
- [ ] Migration timeline scheduled (date, duration, downtime window)
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Data backup created
- [ ] Test migration completed on non-prod environment

**Technical:**
- [ ] Source database accessible
- [ ] Target Q-Docs database created and empty
- [ ] Network connectivity verified
- [ ] Disk space sufficient for temporary files
- [ ] Database credentials available
- [ ] SQL clients installed (psql, pgAdmin, or DBeaver)
- [ ] All dependencies installed (Python, sqlalchemy, pandas)

**Data Quality:**
- [ ] Source data audited for completeness
- [ ] Known data issues documented
- [ ] Field mapping created (source → Q-Docs)
- [ ] Data validation rules defined
- [ ] User account mapping prepared
- [ ] Document structure planned

**Approval:**
- [ ] Technical lead approval obtained
- [ ] Data owner sign-off received
- [ ] Compliance/Security review completed
- [ ] Executive notification sent

---

## Migration Scenarios

### Scenario 1: Fresh Installation (No Migration)

**Best for:** New system deployment, greenfield project

**Steps:**

```bash
# 1. Setup clean database
docker-compose up -d db

# 2. Initialize schema
docker-compose exec backend alembic upgrade head

# 3. Seed initial data (roles, admin user)
docker-compose exec backend python3 scripts/seed_data.py

# 4. Create initial users via API or admin panel
# See: docs/INSTALLATION_AND_SETUP_GUIDE.md

# 5. Verify installation
curl http://localhost:8000/api/health
```

**Time:** 10-15 minutes

---

### Scenario 2: Importing Users from CSV

**Best for:** Bulk user creation from HR system or spreadsheet

**Preparation:**

Create `users_import.csv`:
```csv
username,email,full_name,role_name,department,is_active
john.doe,john@company.com,John Doe,Author,Quality Assurance,true
jane.smith,jane@company.com,Jane Smith,Reviewer,Operations,true
bob.johnson,bob@company.com,Bob Johnson,Approver,Management,true
```

**Role names:** `Author`, `Reviewer`, `Approver`, `DMS_Admin`

**Migration Script:**

```python
# File: backend/scripts/import_users.py

import csv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import get_password_hash

def import_users_from_csv(csv_file_path):
    db = SessionLocal()
    
    try:
        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if user already exists
                existing_user = db.query(User).filter_by(username=row['username']).first()
                if existing_user:
                    print(f"User {row['username']} already exists, skipping...")
                    continue
                
                # Get role
                role = db.query(Role).filter_by(name=row['role_name']).first()
                if not role:
                    print(f"Role {row['role_name']} not found, skipping user {row['username']}")
                    continue
                
                # Create temporary password
                temp_password = f"TempPass@{row['username'].split('.')[0].upper()}123"
                
                # Create user
                user = User(
                    username=row['username'],
                    email=row['email'],
                    full_name=row['full_name'],
                    hashed_password=get_password_hash(temp_password),
                    role_id=role.id,
                    is_active=row['is_active'].lower() == 'true'
                )
                
                db.add(user)
                print(f"Added user: {row['username']} (role: {row['role_name']})")
        
        db.commit()
        print("✓ User import completed successfully")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error importing users: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 import_users.py <csv_file_path>")
        sys.exit(1)
    
    import_users_from_csv(sys.argv[1])
```

**Run Migration:**

```bash
cd backend
python3 scripts/import_users.py users_import.csv

# Output:
# Added user: john.doe (role: Author)
# Added user: jane.smith (role: Reviewer)
# Added user: bob.johnson (role: Approver)
# ✓ User import completed successfully
```

**Verify:**

```bash
# Check users were created
psql -U q_docs_user -d q_docs_db -c "SELECT username, email, full_name FROM users LIMIT 10;"
```

---

### Scenario 3: Migrating from Legacy DMS

**Best for:** Replacing old document management system

**Step 1: Export Data from Legacy System**

Most systems support these export formats:

```bash
# Example: Export from old system
# Common formats: SQL dump, CSV files, JSON API

# Option A: SQL Dump
mysqldump -u legacy_user -p legacy_db > legacy_backup.sql

# Option B: CSV Export
# Export each table separately
sqlite3 legacy.db ".mode csv"
sqlite3 legacy.db ".output documents.csv"
sqlite3 legacy.db "SELECT * FROM documents;"

# Option C: API Export
curl -u admin:password https://old-dms.company.com/api/export \
  > legacy_export.json
```

**Step 2: Data Mapping**

Create mapping between old and new schemas:

```python
# File: backend/scripts/legacy_migration/field_mapping.py

FIELD_MAPPING = {
    # Old System → Q-Docs
    'doc_id': 'document_number',
    'doc_title': 'title',
    'doc_desc': 'description',
    'doc_status': 'status',  # Map values: Draft→Draft, Approved→Approved, etc.
    'created_by_user': 'owner_id',  # Requires user ID mapping
    'created_date': 'created_at',
    'updated_by_user': 'updated_by_id',
    'updated_date': 'updated_at',
}

USER_MAPPING = {
    # Map old user IDs to new user IDs
    'old_user_123': 'new_user_456',
}

STATUS_MAPPING = {
    'DRAFT': 'Draft',
    'REVIEW': 'Under Review',
    'APPROVED': 'Approved',
    'PUBLISHED': 'Effective',
    'ARCHIVED': 'Archived',
    'REJECTED': 'Rejected',
}
```

**Step 3: Data Transformation**

```python
# File: backend/scripts/legacy_migration/transform_data.py

import json
import pandas as pd
from datetime import datetime
from field_mapping import FIELD_MAPPING, USER_MAPPING, STATUS_MAPPING

def transform_legacy_documents(legacy_json_file, output_file):
    """
    Transform legacy document data to Q-Docs format
    """
    with open(legacy_json_file, 'r') as f:
        legacy_docs = json.load(f)
    
    transformed_docs = []
    
    for old_doc in legacy_docs:
        new_doc = {
            'document_number': old_doc.get('doc_id'),
            'title': old_doc.get('doc_title'),
            'description': old_doc.get('doc_desc'),
            'status': STATUS_MAPPING.get(old_doc.get('doc_status'), 'Draft'),
            'owner_id': USER_MAPPING.get(old_doc.get('created_by_user')),
            'created_at': old_doc.get('created_date'),
            'updated_at': old_doc.get('updated_date'),
            'content': old_doc.get('doc_content', ''),
            'department': old_doc.get('department', 'Uncategorized'),
        }
        
        # Validate required fields
        if new_doc['title'] and new_doc['owner_id']:
            transformed_docs.append(new_doc)
        else:
            print(f"⚠ Skipping document {old_doc.get('doc_id')}: missing required fields")
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(transformed_docs, f, indent=2, default=str)
    
    print(f"✓ Transformed {len(transformed_docs)} documents")
    return transformed_docs

if __name__ == "__main__":
    transform_legacy_documents('legacy_export.json', 'transformed_documents.json')
```

**Step 4: Import Transformed Data**

```python
# File: backend/scripts/legacy_migration/import_legacy.py

import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Document, DocumentVersion, User

def import_transformed_documents(json_file):
    """
    Import transformed document data into Q-Docs
    """
    db = SessionLocal()
    
    try:
        with open(json_file, 'r') as f:
            documents = json.load(f)
        
        for doc_data in documents:
            # Check if document already exists
            existing = db.query(Document).filter_by(
                document_number=doc_data['document_number']
            ).first()
            
            if existing:
                print(f"Document {doc_data['document_number']} already exists, skipping...")
                continue
            
            # Create document
            document = Document(
                document_number=doc_data['document_number'],
                title=doc_data['title'],
                description=doc_data.get('description'),
                status=doc_data['status'],
                owner_id=doc_data['owner_id'],
                created_at=doc_data['created_at'],
                updated_at=doc_data['updated_at'],
                department=doc_data.get('department'),
            )
            
            db.add(document)
            db.flush()  # Get document ID
            
            # Create initial version
            version = DocumentVersion(
                document_id=document.id,
                version_number=1,
                content=doc_data['content'],
                status=doc_data['status'],
                created_by_id=doc_data['owner_id'],
                is_latest=True,
            )
            
            db.add(version)
            print(f"✓ Imported document: {doc_data['document_number']}")
        
        db.commit()
        print(f"✓ Migration completed: {len(documents)} documents imported")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 import_legacy.py <json_file>")
        sys.exit(1)
    
    import_transformed_documents(sys.argv[1])
```

**Run Complete Migration:**

```bash
cd backend/scripts/legacy_migration

# 1. Transform data
python3 transform_data.py legacy_export.json transformed_documents.json

# 2. Import into Q-Docs
cd ..
python3 legacy_migration/import_legacy.py legacy_migration/transformed_documents.json

# 3. Verify (see Data Validation section)
```

---

### Scenario 4: Database Restore from Backup

**Best for:** Disaster recovery, restoring to previous point-in-time

**Backup Existing Database:**

```bash
# Full PostgreSQL backup
pg_dump -U q_docs_user -h localhost q_docs_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -U q_docs_user -h localhost -Fc q_docs_db > backup_$(date +%Y%m%d_%H%M%S).dump

# Docker environment
docker-compose exec db pg_dump -U q_docs_user q_docs_db > backup.sql

# With verbose output
pg_dump -U q_docs_user -h localhost -v q_docs_db > backup_verbose.sql
```

**Restore from Backup:**

```bash
# Create new database
createdb -U q_docs_user restored_q_docs_db

# Restore from SQL dump
psql -U q_docs_user -h localhost restored_q_docs_db < backup_20240220_120000.sql

# Restore from compressed dump
pg_restore -U q_docs_user -h localhost -d restored_q_docs_db backup.dump

# Docker restore
docker-compose exec db psql -U q_docs_user q_docs_db < backup.sql

# Verify restoration
psql -U q_docs_user -d restored_q_docs_db -c "SELECT COUNT(*) as document_count FROM documents;"
```

**Switch Application to Restored Database:**

```bash
# Update .env file
# Change DATABASE_URL to point to restored database
DATABASE_URL=postgresql://q_docs_user:password@localhost:5432/restored_q_docs_db

# Restart application
docker-compose restart backend

# Verify connectivity
curl http://localhost:8000/api/health
```

---

## Exporting Data from Source System

### Method 1: PostgreSQL Native Export

```bash
# Full database dump
pg_dump -U source_user -h source_host source_db > full_backup.sql

# Specific tables
pg_dump -U source_user -h source_host -t documents -t document_versions source_db > documents.sql

# With data only (no schema)
pg_dump -U source_user -h source_host --data-only source_db > data_only.sql

# With schema only
pg_dump -U source_user -h source_host --schema-only source_db > schema_only.sql
```

### Method 2: CSV Export (for non-PostgreSQL systems)

```bash
# SQLite to CSV
sqlite3 source.db ".mode csv"
sqlite3 source.db ".output documents.csv"
sqlite3 source.db "SELECT * FROM documents;"

# MySQL to CSV
SELECT *
INTO OUTFILE '/tmp/documents.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
FROM documents;

# Python pandas method
import pandas as pd
df = pd.read_sql("SELECT * FROM documents", connection)
df.to_csv('documents.csv', index=False)
```

### Method 3: JSON Export

```python
# Python script to export to JSON
import json
from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('postgresql://user:pass@host/database')
metadata = MetaData()
metadata.reflect(bind=engine)

export_data = {}

for table in metadata.tables.values():
    result = engine.execute(table.select())
    export_data[table.name] = [dict(row) for row in result]

with open('export.json', 'w') as f:
    json.dump(export_data, f, indent=2, default=str)
```

---

## Importing Data to Q-Docs

### Method 1: Direct SQL Insertion

```sql
-- Disable foreign key checks temporarily
SET session_replication_role = REPLICA;

-- Insert data
INSERT INTO users (username, email, full_name, role_id, is_active, created_at)
VALUES ('john.doe', 'john@company.com', 'John Doe', 1, true, NOW());

INSERT INTO documents (document_number, title, description, owner_id, status, created_at)
VALUES ('DOC-001', 'Sample Document', 'Description', 1, 'Draft', NOW());

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;
```

### Method 2: Bulk Insert via SQL Dump

```bash
# Restore SQL dump directly
psql -U q_docs_user -d q_docs_db < migrated_data.sql

# Monitor progress
psql -U q_docs_user -d q_docs_db \
  -c "SELECT 'documents' as table_name, COUNT(*) as record_count FROM documents
       UNION ALL
       SELECT 'users', COUNT(*) FROM users
       UNION ALL
       SELECT 'document_versions', COUNT(*) FROM document_versions;"
```

### Method 3: API Bulk Import

```python
# File: backend/scripts/bulk_import_api.py

import requests
import json
from typing import List, Dict

class BulkDocumentImporter:
    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url
        self.session = self._authenticate(username, password)
    
    def _authenticate(self, username: str, password: str):
        """Authenticate and get API token"""
        response = requests.post(
            f"{self.api_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        token = response.json()['access_token']
        
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {token}'})
        return session
    
    def import_documents(self, documents: List[Dict]):
        """Import multiple documents"""
        created_count = 0
        failed_count = 0
        
        for doc in documents:
            try:
                response = self.session.post(
                    f"{self.api_url}/api/v1/documents",
                    json=doc
                )
                
                if response.status_code in [200, 201]:
                    created_count += 1
                    print(f"✓ Created: {doc['title']}")
                else:
                    failed_count += 1
                    print(f"✗ Failed: {doc['title']} - {response.text}")
            
            except Exception as e:
                failed_count += 1
                print(f"✗ Error with {doc['title']}: {str(e)}")
        
        print(f"\nImport Summary: {created_count} created, {failed_count} failed")
        return created_count, failed_count

# Usage
if __name__ == "__main__":
    # Load documents from JSON
    with open('documents_to_import.json', 'r') as f:
        documents = json.load(f)
    
    importer = BulkDocumentImporter(
        api_url="http://localhost:8000",
        username="admin",
        password="admin_password"
    )
    
    importer.import_documents(documents)
```

---

## Data Validation

### Validation Checklist

After migration, verify data integrity:

```bash
# 1. Count records
psql -U q_docs_user -d q_docs_db << EOF
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Documents', COUNT(*) FROM documents
UNION ALL
SELECT 'Document Versions', COUNT(*) FROM document_versions
UNION ALL
SELECT 'Comments', COUNT(*) FROM comments
UNION ALL
SELECT 'Attachments', COUNT(*) FROM attachments
UNION ALL
SELECT 'Audit Logs', COUNT(*) FROM audit_logs;
EOF

# 2. Check for orphaned records (versions without documents)
psql -U q_docs_user -d q_docs_db << EOF
SELECT dv.id as orphaned_version_id
FROM document_versions dv
LEFT JOIN documents d ON dv.document_id = d.id
WHERE d.id IS NULL;
EOF

# 3. Check for missing documents
psql -U q_docs_user -d q_docs_db << EOF
SELECT id, title FROM documents
WHERE owner_id NOT IN (SELECT id FROM users);
EOF

# 4. Verify foreign key constraints
psql -U q_docs_user -d q_docs_db << EOF
SELECT constraint_type, COUNT(*) 
FROM information_schema.table_constraints 
WHERE table_schema = 'public'
GROUP BY constraint_type;
EOF
```

### Python Validation Script

```python
# File: backend/scripts/validate_migration.py

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Document, DocumentVersion, User, Comment

def validate_migration():
    """Validate data integrity after migration"""
    db = SessionLocal()
    issues = []
    
    try:
        # Count records
        user_count = db.query(User).count()
        doc_count = db.query(Document).count()
        version_count = db.query(DocumentVersion).count()
        comment_count = db.query(Comment).count()
        
        print("=" * 50)
        print("MIGRATION VALIDATION REPORT")
        print("=" * 50)
        print(f"Users: {user_count}")
        print(f"Documents: {doc_count}")
        print(f"Document Versions: {version_count}")
        print(f"Comments: {comment_count}")
        print()
        
        # Check for orphaned records
        print("Checking for orphaned records...")
        orphaned_versions = db.query(DocumentVersion).filter(
            ~DocumentVersion.document_id.in_(
                db.query(Document.id)
            )
        ).count()
        
        if orphaned_versions > 0:
            issues.append(f"Found {orphaned_versions} orphaned document versions")
            print(f"⚠ {orphaned_versions} orphaned versions found")
        else:
            print("✓ No orphaned versions")
        
        # Check for missing owners
        print("\nChecking for documents with missing owners...")
        missing_owners = db.query(Document).filter(
            ~Document.owner_id.in_(
                db.query(User.id)
            )
        ).count()
        
        if missing_owners > 0:
            issues.append(f"Found {missing_owners} documents with missing owners")
            print(f"⚠ {missing_owners} documents have invalid owners")
        else:
            print("✓ All documents have valid owners")
        
        # Check document status values
        print("\nValidating document statuses...")
        valid_statuses = ['Draft', 'Under Review', 'Pending Approval', 'Approved', 'Effective', 'Archived', 'Obsolete', 'Rejected']
        invalid_statuses = db.query(Document).filter(
            ~Document.status.in_(valid_statuses)
        ).count()
        
        if invalid_statuses > 0:
            issues.append(f"Found {invalid_statuses} documents with invalid status")
            print(f"⚠ {invalid_statuses} invalid statuses found")
        else:
            print("✓ All document statuses valid")
        
        # Summary
        print("\n" + "=" * 50)
        if issues:
            print(f"VALIDATION FAILED: {len(issues)} issues found")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("VALIDATION SUCCESSFUL ✓")
            return True
    
    finally:
        db.close()

if __name__ == "__main__":
    success = validate_migration()
    exit(0 if success else 1)
```

**Run Validation:**

```bash
cd backend
python3 scripts/validate_migration.py
```

---

## Rollback Procedures

### Complete Rollback (Delete All Migrated Data)

⚠️ **WARNING: This deletes all data!**

```bash
# Create backup FIRST
pg_dump -U q_docs_user q_docs_db > backup_before_rollback.sql

# Option 1: Delete all data but keep schema
psql -U q_docs_user -d q_docs_db << EOF
TRUNCATE TABLE audit_logs CASCADE;
TRUNCATE TABLE comments CASCADE;
TRUNCATE TABLE attachments CASCADE;
TRUNCATE TABLE document_versions CASCADE;
TRUNCATE TABLE documents CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE roles CASCADE;
EOF

# Option 2: Restore from pre-migration backup
psql -U q_docs_user -d q_docs_db < pre_migration_backup.sql

# Option 3: Drop and recreate database
dropdb q_docs_db
createdb q_docs_db
psql -U q_docs_user -d q_docs_db < pre_migration_backup.sql

# Re-initialize application
docker-compose restart backend
```

### Partial Rollback (Remove Specific Documents)

```sql
-- Delete documents imported in this migration
DELETE FROM documents
WHERE document_number LIKE 'LEGACY-%'
AND created_at > '2024-02-20 10:00:00';

-- Cascade will automatically delete:
-- - document_versions
-- - comments
-- - attachments
-- - audit logs related to these documents
```

---

## Troubleshooting Migration Issues

### Issue: "Constraint Violation - Foreign Key Error"

**Cause:** Referenced record doesn't exist in parent table

**Solution:**
```sql
-- Check constraint violations
SELECT constraint_type, COUNT(*)
FROM information_schema.table_constraints
WHERE table_schema = 'public'
GROUP BY constraint_type;

-- Temporarily disable constraints
ALTER TABLE documents DISABLE TRIGGER ALL;
-- Import data
ALTER TABLE documents ENABLE TRIGGER ALL;

-- Or use:
SET CONSTRAINTS ALL DEFERRED;
-- Import data
SET CONSTRAINTS ALL IMMEDIATE;
```

### Issue: "Duplicate Key Violation"

**Cause:** Record with same unique value already exists

**Solution:**
```sql
-- Check for duplicates
SELECT document_number, COUNT(*)
FROM documents
GROUP BY document_number
HAVING COUNT(*) > 1;

-- Remove duplicates
DELETE FROM documents d1
WHERE d1.id NOT IN (
    SELECT MIN(id)
    FROM documents d2
    GROUP BY d2.document_number
);
```

### Issue: "Out of Memory During Large Import"

**Cause:** Importing very large datasets at once

**Solution:**
```bash
# Split import into batches
split -l 10000 large_data.sql large_data_part_

# Import in batches
for file in large_data_part_*; do
    echo "Importing $file..."
    psql -U q_docs_user q_docs_db < $file
done

# Or use batch import script
python3 scripts/batch_import.py --batch-size 1000 data.json
```

### Issue: "Migration Slower Than Expected"

**Cause:** Missing indexes, slow network, limited resources

**Solution:**
```sql
-- Disable indexes temporarily
ALTER INDEX idx_document_number UNUSABLE;

-- Import data (faster)

-- Rebuild indexes
REINDEX INDEX idx_document_number;
ALTER INDEX idx_document_number REBUILD;

-- Monitor progress
SELECT query, state, query_start
FROM pg_stat_activity
WHERE state != 'idle';
```

### Issue: "Character Encoding Problems"

**Cause:** Data has incompatible character encoding

**Solution:**
```bash
# Check target database encoding
psql -U q_docs_user -l | grep q_docs_db

# Dump with specific encoding
pg_dump -U q_docs_user --encoding=UTF8 q_docs_db > dump.sql

# Convert file encoding if needed
iconv -f ISO-8859-1 -t UTF-8 input.sql > output.sql

# Import with encoding specified
psql -U q_docs_user -d q_docs_db --set=client_encoding=UTF8 < dump.sql
```

---

## Post-Migration Verification

### Step 1: System Health Check

```bash
# Health endpoint
curl http://localhost:8000/api/health

# Check API responds
curl -X GET http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Check database connectivity
psql -U q_docs_user -d q_docs_db -c "SELECT version();"
```

### Step 2: Data Spot Checks

```bash
# Login with migrated user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"migrated_user","password":"password"}'

# Retrieve document
curl -X GET http://localhost:8000/api/v1/documents/DOC-001 \
  -H "Authorization: Bearer TOKEN"

# Check audit logs
curl -X GET http://localhost:8000/api/v1/audit-logs \
  -H "Authorization: Bearer TOKEN"
```

### Step 3: Application Testing

```bash
# Test document creation
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Test Doc",
    "description":"Post-migration test",
    "owner_id":1
  }'

# Test document approval workflow
# (through UI or API calls)

# Test search functionality  
curl -X GET "http://localhost:8000/api/v1/documents?search=migrated"
```

### Step 4: Performance Baseline

```bash
# Response time test
time curl http://localhost:8000/api/v1/documents?limit=100

# Database query performance
psql -U q_docs_user -d q_docs_db << EOF
EXPLAIN ANALYZE
SELECT * FROM documents WHERE owner_id = 1;
EOF

# Monitor resource usage
docker stats

# Check logs for errors
docker-compose logs backend | grep ERROR
```

---

## Migration Best Practices

### Before Migration

✅ **DO:**
- Test migration on non-production database
- Create complete database backups
- Document all field mappings
- Verify data quality in source system
- Schedule during maintenance window
- Notify users of downtime
- Have rollback plan ready

❌ **DON'T:**
- Migrate during business hours without warning
- Modify source data during export
- Skip validation steps
- Assume data is perfect
- Forget about foreign key constraints
- Leave authentication tokens exposed
- Use production passwords in scripts

### During Migration

✅ **DO:**
- Monitor migration progress
- Log all actions and errors
- Keep timestamps for troubleshooting
- Perform incremental validation
- Have database team on standby

❌ **DON'T:**
- Make manual database edits while migration running
- Close terminal/script before completion
- Ignore warnings or errors
- Interrupt the process

### After Migration

✅ **DO:**
- Run complete validation suite
- Test all major workflows
- Check user access and permissions
- Monitor system performance
- Update documentation
- Communicate completion status
- Archive migration scripts and logs

❌ **DON'T:**
- Delete source data immediately
- Skip user acceptance testing
- Remove old system access immediately
- Forget to update application settings

---

## Performance Optimization

### For Large Migrations (100K+ records)

```python
# Use bulk operations for better performance
from sqlalchemy import insert

# Batch insert instead of adding one by one
def bulk_insert_documents(documents_list, batch_size=1000):
    for i in range(0, len(documents_list), batch_size):
        batch = documents_list[i:i+batch_size]
        db.execute(
            insert(Document).values(batch)
        )
        db.commit()
        print(f"Inserted {i+len(batch)}/{len(documents_list)} records")
```

### Index Strategy

```sql
-- Create indexes AFTER migration (faster)
CREATE INDEX idx_documents_owner_id ON documents(owner_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_document_versions_doc_id ON document_versions(document_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

-- Vacuum and analyze for query optimization
VACUUM ANALYZE;
```

---

## Monitoring Migration Progress

### Real-time Progress Script

```python
# File: backend/scripts/monitor_migration.py

import time
import psycopg2
from datetime import datetime

def monitor_migration():
    """Monitor migration progress in real-time"""
    
    conn = psycopg2.connect(
        "postgresql://q_docs_user:password@localhost/q_docs_db"
    )
    cursor = conn.cursor()
    
    while True:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users) as users,
                (SELECT COUNT(*) FROM documents) as documents,
                (SELECT COUNT(*) FROM document_versions) as versions,
                (SELECT COUNT(*) FROM comments) as comments,
                (SELECT COUNT(*) FROM attachments) as attachments
        """)
        
        row = cursor.fetchone()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Migration Progress:")
        print(f"  Users:     {row[0]:,}")
        print(f"  Documents: {row[1]:,}")
        print(f"  Versions:  {row[2]:,}")
        print(f"  Comments:  {row[3]:,}")
        print(f"  Attachments: {row[4]:,}")
        
        time.sleep(5)  # Refresh every 5 seconds

if __name__ == "__main__":
    try:
        monitor_migration()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
```

---

## Support & Resources

- **Database Docs:** [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- **SQLAlchemy:** [SQLAlchemy ORM Guide](https://docs.sqlalchemy.org/)
- **Pandas:** [Pandas Data Manipulation](https://pandas.pydata.org/docs/)
- **Migration Issues:** Contact DMS support team

---

**Version:** 1.0.0 | **Last Updated:** February 2026 | **Next Review:** August 2026
