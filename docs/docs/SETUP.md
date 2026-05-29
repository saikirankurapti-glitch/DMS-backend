# Setup Guide - Pharma DMS

Complete guide for setting up and running the Pharma Document Management System locally.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Manual Setup](#manual-setup)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For Docker Setup (Recommended)

- Docker 20.10+
- Docker Compose 2.0+

### For Manual Setup

- Python 3.11 or higher
- PostgreSQL 15+ (or SQLite for development)
- pip (Python package manager)
- virtualenv or venv

### Development Tools (Optional)

- Git
- Postman or Insomnia (API testing)
- VS Code or PyCharm (IDE)

---

## Quick Start with Docker

The fastest way to get started is using Docker Compose.

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd DMS
```

### Step 2: Start Services

```bash
docker-compose up -d
```

This command will:
- Start PostgreSQL database
- Start FastAPI backend
- Initialize database with tables
- Seed initial roles and admin user
- Start pgAdmin (optional database management tool)

### Step 3: Verify Services

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs backend
```

### Step 4: Access Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **pgAdmin**: http://localhost:5050 (admin@pharma-dms.com / admin)

### Step 5: Login

Default admin credentials:
- **Username**: `admin`
- **Password**: `Admin@123456`

⚠️ **Important:** Change the admin password immediately after first login!

### Stopping Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v
```

---

## Manual Setup

Follow these steps for a manual installation without Docker.

### Step 1: Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Use your preferred text editor
nano .env
```

### Step 4: Setup Database

#### Option A: SQLite (Development Only)

```bash
# In .env file, set:
DATABASE_URL=sqlite:///./dms.db

# Initialize database
python scripts/init_db.py
```

#### Option B: PostgreSQL (Recommended)

```bash
# Install PostgreSQL 15+
# Create database and user

# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE dms_db;
CREATE USER dms_user WITH PASSWORD 'dms_password';
GRANT ALL PRIVILEGES ON DATABASE dms_db TO dms_user;
\q

# In .env file, set:
DATABASE_URL=postgresql://dms_user:dms_password@localhost:5432/dms_db

# Initialize database
python scripts/init_db.py
```

### Step 5: Run Application

```bash
uvicorn app.main:app --reload

# Or specify host and port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Access Application

Open http://localhost:8000/api/docs in your browser.

---

## Database Setup

### Using Alembic Migrations

The project uses Alembic for database migrations.

#### Create a Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to user"

# Or create empty migration
alembic revision -m "Custom migration"
```

#### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# View current version
alembic current

# View migration history
alembic history
```

#### Rollback Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

### Reset Database

⚠️ **Warning:** This will delete all data!

```bash
cd backend
python scripts/reset_db.py
```

### Seed Data

To add initial roles and admin user:

```bash
cd backend
python scripts/init_db.py
```

---

## Configuration

### Environment Variables

Edit `.env` file in the `backend` directory:

#### Application Settings

```bash
APP_NAME="Pharma DMS"
APP_VERSION="1.0.0"
ENVIRONMENT="development"  # development, staging, production
DEBUG=True                 # Set to False in production
```

#### Security Settings

```bash
# Generate a secure secret key (min 32 characters)
SECRET_KEY="your-secure-secret-key-change-in-production"

# JWT token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Hashing algorithm
ALGORITHM="HS256"
```

#### Database Settings

```bash
# PostgreSQL
DATABASE_URL="postgresql://dms_user:dms_password@localhost:5432/dms_db"

# SQLite (development only)
# DATABASE_URL="sqlite:///./dms.db"
```

#### CORS Settings

```bash
# Comma-separated list of allowed origins
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

#### Initial Admin User

```bash
FIRST_ADMIN_USERNAME="admin"
FIRST_ADMIN_EMAIL="admin@pharma-dms.com"
FIRST_ADMIN_PASSWORD="Admin@123456"
```

#### Password Policy

```bash
MIN_PASSWORD_LENGTH=8
REQUIRE_PASSWORD_CHANGE_ON_RESET=True
```

#### Audit Log Settings

```bash
# Retention period in days
AUDIT_LOG_RETENTION_DAYS=2555  # ~7 years for pharma compliance
```

### Generating a Secure Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

---

## Running the Application

### Development Mode

```bash
cd backend

# With auto-reload
uvicorn app.main:app --reload

# With custom host and port
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Production Mode

```bash
cd backend

# Using Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Background Service (Linux)

Create systemd service file: `/etc/systemd/system/dms.service`

```ini
[Unit]
Description=Pharma DMS API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/DMS/backend
Environment="PATH=/path/to/DMS/backend/venv/bin"
ExecStart=/path/to/DMS/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dms
sudo systemctl start dms
sudo systemctl status dms
```

---

## Testing

### Manual Testing

#### 1. Using Swagger UI

1. Open http://localhost:8000/api/docs
2. Click "Authorize" button
3. Enter credentials and login
4. Copy the access token
5. Click "Authorize" again and paste token
6. Test endpoints

#### 2. Using cURL

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123456"}'

# Save token
TOKEN="<paste_token_here>"

# Create user
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test@123",
    "first_name": "Test",
    "last_name": "User",
    "role_ids": [1]
  }'

# List users
curl -X GET "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. Using Postman

1. Import OpenAPI spec from http://localhost:8000/api/openapi.json
2. Create environment with `base_url` and `token` variables
3. Test endpoints

### Automated Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000

# Kill process (replace PID)
# Windows
taskkill /PID <pid> /F

# Linux/macOS
kill -9 <pid>
```

#### 2. Database Connection Error

**SQLite:**
```bash
# Check file permissions
ls -la dms.db

# Recreate database
rm dms.db
python scripts/init_db.py
```

**PostgreSQL:**
```bash
# Check PostgreSQL is running
# Linux
sudo systemctl status postgresql

# Check connection
psql -U dms_user -d dms_db -h localhost

# Verify DATABASE_URL in .env
```

#### 3. Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Migration Errors

```bash
# Check current migration status
alembic current

# Reset migrations (⚠️ deletes data)
alembic downgrade base
alembic upgrade head

# Or reset database
python scripts/reset_db.py
```

#### 5. Authentication Errors

```bash
# Verify token is valid
# Check token expiration time in .env
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Verify SECRET_KEY is consistent
# Don't change SECRET_KEY after tokens are issued
```

#### 6. Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f backend

# Reset everything (⚠️ deletes volumes)
docker-compose down -v
docker-compose up -d
```

### Getting Help

1. **Check Logs:**
   ```bash
   # Docker
   docker-compose logs backend
   
   # Manual
   # Logs appear in console with --reload
   ```

2. **Enable Debug Mode:**
   ```bash
   # In .env
   DEBUG=True
   ```

3. **Check API Documentation:**
   - http://localhost:8000/api/docs

4. **Verify Environment:**
   ```bash
   python --version  # Should be 3.11+
   pip list          # Check installed packages
   ```

---

## Next Steps

After successful setup:

1. **Change Admin Password**
   - Login with default credentials
   - Use password reset endpoint

2. **Create Test Users**
   - Create users with different roles
   - Test role-based access control

3. **Review Audit Logs**
   - Check audit log endpoint
   - Verify all actions are logged

4. **Explore API**
   - Review interactive documentation
   - Test all endpoints

5. **Production Deployment**
   - See deployment guide (if available)
   - Configure production settings
   - Setup SSL/TLS certificates
   - Configure reverse proxy (nginx)
   - Setup backup strategy

---

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Change admin password
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/SSL
- [ ] Setup reverse proxy (nginx/Apache)
- [ ] Configure database backups
- [ ] Setup monitoring and logging
- [ ] Review and harden security settings
- [ ] Setup firewall rules
- [ ] Enable rate limiting
- [ ] Configure email notifications (future)
- [ ] Setup disaster recovery plan
- [ ] Document production architecture
- [ ] Perform security audit

---

## Additional Resources

- **API Documentation**: [docs/API.md](./API.md)
- **User Stories**: [docs/USER_STORIES.md](./USER_STORIES.md)
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/


