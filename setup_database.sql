-- PostgreSQL Database Setup Script for Pharma DMS
-- Execute this script to create the database for DMS

-- Connect as postgres superuser and run:
-- psql -U postgres -p 5433

-- Create database
CREATE DATABASE dms_db;

-- Grant privileges (postgres user already exists, just grant privileges)
GRANT ALL PRIVILEGES ON DATABASE dms_db TO postgres;

-- Connect to the new database
\c dms_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO postgres;

-- Display confirmation
\echo 'Database dms_db created successfully!'
\echo 'Connection details:'
\echo '  Host: localhost'
\echo '  Port: 5433'
\echo '  Database: dms_db'
\echo '  Username: postgres'
\echo ''
\echo 'Next steps:'
\echo '1. Exit psql with: \q'
\echo '2. Initialize database: cd backend && python scripts/init_db.py'
\echo '3. Start application: uvicorn app.main:app --reload'


