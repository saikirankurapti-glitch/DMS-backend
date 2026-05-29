# Installation & Setup Guide - Q-Docs System

Complete step-by-step guide for installing, configuring, and deploying the Q-Docs Document Management System for the first time.

---

## Table of Contents

1. [Pre-Installation Checklist](#pre-installation-checklist)
2. [System Requirements](#system-requirements)
3. [Quick Start with Docker (Recommended)](#quick-start-with-docker-recommended)
4. [Manual Installation (Linux/Windows)](#manual-installation-linuxwindows)
5. [Configuration Guide](#configuration-guide)
6. [Database Setup](#database-setup)
7. [Initial System Setup](#initial-system-setup)
8. [Testing the Installation](#testing-the-installation)
9. [Troubleshooting Installation Issues](#troubleshooting-installation-issues)
10. [Next Steps (Production Deployment)](#next-steps-production-deployment)

---

## Pre-Installation Checklist

Before starting installation, verify:

- [ ] You have admin/root access to the server
- [ ] Operating system is Linux, Windows, or macOS
- [ ] Internet connection is available for downloading dependencies
- [ ] Firewall ports are open (8000 for API, 5432 for database, 5050 for pgAdmin)
- [ ] You have at least 2GB of disk space
- [ ] You have the repository code/files ready
- [ ] Database name and credentials are prepared
- [ ] SMTP credentials for email notifications (if needed)
- [ ] SSL certificate (for production deployment)

---

## System Requirements

### Minimum Requirements (Development)

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, Ubuntu 20.04+, CentOS 8+, macOS 11+ |
| **CPU** | 2 cores minimum |
| **RAM** | 4 GB minimum (8GB recommended) |
| **Storage** | 20 GB free space |
| **Python** | 3.11.0 or higher |
| **Database** | PostgreSQL 14+ or SQLite (dev only) |

### Recommended (Production)

| Component | Specification |
|-----------|---------------|
| **OS** | Ubuntu 22.04 LTS or CentOS 8+ |
| **CPU** | 4+ cores |
| **RAM** | 16 GB minimum |
| **Storage** | 100+ GB (SSD recommended) |
| **Database** | PostgreSQL 15+ |
| **Backup Storage** | Separate disk/cloud location |
| **Load Balancer** | nginx, HAProxy, or cloud LB |

### Software Dependencies

**For Docker Installation:**
- Docker 20.10+
- Docker Compose 2.0+

**For Manual Installation:**
- Python 3.11+
- pip (Python package manager)
- PostgreSQL 14+ (or SQLite for dev)
- Git (for cloning repository)

**Optional:**
- Postman or Insomnia (API testing)
- DBeaver or pgAdmin (database management)
- VS Code or PyCharm (IDE for development)

---

## Quick Start with Docker (Recommended)

The easiest way to get started. All services run in containers.

### Step 1: Install Docker

**Windows:**
1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. Follow installation prompts, accept defaults
4. Restart your computer

**Linux (Ubuntu/Debian):**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker run hello-world
```

**macOS:**
1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Open the .dmg file and drag Docker to Applications
3. Launch Docker from Applications
4. Follow setup wizard

### Step 2: Get the Project Code

**Option A: Clone from Git Repository**
```bash
# Clone the repository
git clone https://github.com/yourcompany/q-docs.git
cd q-docs

# Navigate to project root
pwd
# Should show: /path/to/q-docs
```

**Option B: Extract from ZIP/Archive**
```bash
# Extract the provided archive
unzip q-docs-v1.0.0.zip
cd q-docs
```

### Step 3: Create Environment File

Create `.env` file in project root with configuration:

```bash
# Navigate to project root
cd q-docs

# Create .env file (Windows PowerShell)
echo "" > .env

# Or Linux/Mac
touch .env
```

**Edit .env file** with these variables:

```env
# APPLICATION
APP_NAME=Q-Docs
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key-here-minimum-32-characters-long-use-random-string

# DATABASE
DATABASE_URL=postgresql://q_docs_user:secure_password_123@db:5432/q_docs_db
DATABASE_POOL_SIZE=20
DATABASE_POOL_PRELOAD=5

# SECURITY
JWT_SECRET_KEY=your-jwt-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
SESSION_TIMEOUT_MINUTES=480

# ADMIN USER (Initial)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@q-docs.local
ADMIN_PASSWORD=TempPassword@123456

# EMAIL (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@q-docs.local
SMTP_FROM_NAME=Q-Docs System

# OPTIONAL: AI Features
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=your-anthropic-key-here

# CORS (For development)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# REDIS (For caching - optional)
REDIS_URL=redis://redis:6379/0

# POSTGRES ADMIN
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_admin_password
POSTGRES_DB=q_docs_db
```

### Step 4: Start Services with Docker Compose

```bash
# Start all services (backend, database, pgAdmin)
docker-compose up -d

# Check running containers
docker-compose ps

# View logs
docker-compose logs -f backend

# Wait for startup (usually 30-60 seconds)
```

**Expected output:**
```
CONTAINER ID   IMAGE           STATUS       PORTS
abc123         q-docs:latest   Up 1 min     0.0.0.0:8000->8000/tcp
def456         postgres:15     Up 1 min     0.0.0.0:5432->5432/tcp
ghi789         pgadmin:latest  Up 1 min     0.0.0.0:5050->80/tcp
```

### Step 5: Verify Installation

**Access the system:**

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs (interactive)
- **Database Admin**: http://localhost:5050

**Login to API Docs:**
- Click "Authorize" button
- Username: `admin`
- Password: `TempPassword@123456` (or whatever you set)

**Test an endpoint:**
1. Go to http://localhost:8000/api/docs
2. Click on "POST /api/v1/auth/login"
3. Click "Try it out"
4. Enter:
   ```json
   {
     "username": "admin",
     "password": "TempPassword@123456"
   }
   ```
5. Click "Execute"
6. Should see `200` response with access token

### Step 6: Access pgAdmin (Database Management)

pgAdmin allows you to manage the database via a web interface:

1. Go to http://localhost:5050
2. Login: `admin@pharma-dms.com` / `admin`
3. Click "Servers" in left sidebar
4. Right-click "Servers" → "Create" → "Server"
5. Fill in:
   - Name: `Q-Docs Local`
   - Host: `db` (Docker service name)
   - Port: `5432`
   - Username: `q_docs_user`
   - Password: `secure_password_123` (from .env)
6. Click "Save"
7. Browse the database structure

### Docker Compose Commands Reference

```bash
# Start all services
docker-compose up -d

# Stop services (data preserved)
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including database
docker-compose down -v

# Rebuild images (after code changes)
docker-compose up -d --build

# Execute command in running container
docker-compose exec backend bash

# Check resource usage
docker stats
```

---

## Manual Installation (Linux/Windows)

For environments where Docker is not available or preferred.

### Step 1: Install Python

**Windows:**
1. Download [Python 3.11+](https://www.python.org/downloads/)
2. Run installer
3. ✅ **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

**Linux (Ubuntu/Debian):**
```bash
# Update package manager
sudo apt update
sudo apt upgrade -y

# Install Python and tools
sudo apt install python3.11 python3-pip python3-venv git build-essential

# Verify installation
python3 --version
pip3 --version
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11
python3 --version
pip3 --version
```

### Step 2: Install PostgreSQL

**Windows:**
1. Download [PostgreSQL 15](https://www.postgresql.org/download/windows/)
2. Run installer
3. Choose installation directory
4. Set postgres user password (remember this!)
5. Keep port as 5432
6. Complete installation
7. Verify:
   ```powershell
   psql --version
   ```

**Linux (Ubuntu/Debian):**
```bash
# Install PostgreSQL
sudo apt install postgresql-15 postgresql-contrib-15

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify
psql --version
```

**macOS:**
```bash
# Install via Homebrew
brew install postgresql@15

# Start service
brew services start postgresql@15

# Verify
psql --version
```

### Step 3: Create Database & User

```bash
# Connect to PostgreSQL (Linux/Mac)
sudo -u postgres psql

# For Windows, open Command Prompt and run:
psql -U postgres

# Then in PostgreSQL prompt, run:
```

```sql
-- Create database
CREATE DATABASE q_docs_db CASCADE;

-- Create user with password
CREATE USER q_docs_user WITH PASSWORD 'secure_password_123';
ALTER ROLE q_docs_user SET client_encoding TO 'utf8';
ALTER ROLE q_docs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE q_docs_user SET default_transaction_deferrable TO on;
ALTER ROLE q_docs_user SET timezone TO 'UTC';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE q_docs_db TO q_docs_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO q_docs_user;

-- Exit psql
\q
```

### Step 4: Clone Project & Create Virtual Environment

```bash
# Clone or extract project
git clone https://github.com/yourcompany/q-docs.git
cd q-docs

# Create virtual environment (Linux/Mac)
python3 -m venv venv
source venv/bin/activate

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Verify activation (you should see (venv) in prompt)
which python
# or
where python
```

### Step 5: Install Python Dependencies

```bash
# Ensure pip is latest
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r backend/requirements.txt

# Verify installation
pip list | grep Flask
# or for FastAPI:
pip list | grep fastapi
```

### Step 6: Setup Configuration Files

```bash
# Navigate to backend directory
cd backend

# Copy example env file
cp .env.example .env
# or on Windows:
copy .env.example .env

# Edit .env file with your settings
# See "Configuration Guide" section below
```

### Step 7: Initialize Database

```bash
# Run migrations (creates tables)
alembic upgrade head

# Seed initial data (roles, admin user)
python -c "from scripts.seed_data import seed_initial_data; seed_initial_data()"

# Check database (optional)
psql -U q_docs_user -d q_docs_db -c "SELECT * FROM users LIMIT 5;"
```

### Step 8: Start Backend Server

```bash
# From backend directory with virtual environment activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Should show:
# Uvicorn running on http://0.0.0.0:8000
```

### Step 9: Test Installation

```bash
# In another terminal, test the API
curl http://localhost:8000/api/v1/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TempPassword@123456"}'

# Should return JSON with access_token
```

---

## Configuration Guide

### Environment Variables Explained

#### Application Settings

```env
# Unique identifier for application requests
APP_NAME=Q-Docs

# Environment: development, staging, production
APP_ENV=production

# Debug mode: false for production
APP_DEBUG=false

# 32+ character random string (use: openssl rand -base64 32)
APP_SECRET_KEY=your-secret-key-here
```

#### Database Configuration

```env
# PostgreSQL connection string
# Format: postgresql://username:password@host:port/database
DATABASE_URL=postgresql://q_docs_user:secure_password_123@db:5432/q_docs_db

# Connection pooling settings
DATABASE_POOL_SIZE=20          # Max connections
DATABASE_POOL_PRELOAD=5        # Pre-create connections
DATABASE_MAX_OVERFLOW=10       # Additional overflow connections
```

#### Security Settings

```env
# JWT token secret (32+ random characters)
JWT_SECRET_KEY=your-jwt-secret-here

# Algorithm for token signing
JWT_ALGORITHM=HS256

# Token expiration time in hours
JWT_EXPIRATION_HOURS=8

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES=480
```

#### Email Configuration (SMTP)

For email notifications to work:

```env
# Gmail example
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# Office 365 example
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.onmicrosoft.com
SMTP_PASSWORD=your-password

# Custom server example
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourcompany.com
SMTP_PASSWORD=secure-password

# Sender details
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Q-Docs System
```

**Gmail Setup (if using Gmail):**
1. Enable 2-Factor Authentication
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate app password for "Mail"
4. Use generated password in SMTP_PASSWORD

#### Admin User (Initial Setup)

```env
# First admin user (created during initialization)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=TempPassword@123456
```

⚠️ **IMPORTANT:** Change admin password immediately after first login!

#### Optional: AI Features

```env
# OpenAI for document summarization
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Anthropic as alternative
ANTHROPIC_API_KEY=your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

#### CORS Configuration

```env
# Allowed origins for frontend (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://q-docs.company.com

# Also allow credentials
CORS_ALLOW_CREDENTIALS=true
```

### Generating Secure Keys

```bash
# Generate SECRET_KEY and JWT_SECRET_KEY
# Linux/Mac:
openssl rand -base64 32

# Windows PowerShell:
[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# Python (any system):
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database Setup

### Automatic Setup (Recommended)

During startup, the application automatically:
1. Creates all tables from SQLAlchemy models
2. Creates indexes for performance
3. Initializes roles (Author, Reviewer, Approver, DMS_Admin)
4. Creates initial admin user

**No manual SQL commands needed!**

### Manual Database Setup (If Needed)

```bash
# From backend directory:

# Create tables
alembic upgrade head

# If you need to downgrade:
alembic downgrade -1

# View migration history
alembic history

# Create specific tables manually
python3 -c "from app.database import Base, engine; Base.metadata.create_all(engine)"
```

### Database Migrations

After code changes that modify models:

```bash
# Generate new migration
alembic revision --autogenerate -m "Add new field to users"

# Review generated migration
cat alembic/versions/xxxxx_add_new_field.py

# Apply migration
alembic upgrade head
```

### Database Backup

```bash
# Backup PostgreSQL database
pg_dump -U q_docs_user q_docs_db > backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
psql -U q_docs_user q_docs_db < backup-20240220-120000.sql

# For Docker:
docker-compose exec db pg_dump -U q_docs_user q_docs_db > backup.sql
```

---

## Initial System Setup

### First Login & Admin Setup

1. **Access the API:**
   ```
   http://localhost:8000/api/docs
   ```

2. **Login with initial credentials:**
   - Username: `admin`
   - Password: `TempPassword@123456`

3. **Change admin password immediately:**
   ```
   GET /api/v1/users/me  (to view profile)
   PUT /api/v1/users/{user_id}  (to change password)
   ```

### Create Department Structure

Use the API to create departments:

```bash
# Example: Create departments
curl -X POST http://localhost:8000/api/v1/departments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Quality Assurance","description":"QA Department"}'
```

### Create Initial Users

```bash
# Create user via API
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username":"john.doe",
    "email":"john@company.com",
    "full_name":"John Doe",
    "role_id":1,
    "department_id":1
  }'
```

### Setup Email Templates

Email templates are on disk at `backend/app/templates/emails/`. Customize:
- `document_assigned_review.html`
- `review_feedback.html`
- `document_approved.html`
- etc.

---

## Testing the Installation

### API Health Check

```bash
# Test API is running
curl http://localhost:8000/api/health

# Response should be:
# {"status":"healthy"}
```

### Database Connectivity

```bash
# Test database connection
curl http://localhost:8000/api/v1/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TempPassword@123456"}'

# Should return access token
```

### Using Postman for Testing

1. **Import collection:**
   - Open Postman
   - File → Import → Select `postman_collection.json`

2. **Setup environment:**
   - Click "Environments"
   - Create new environment "Q-Docs Local"
   - Set variable `url` = `http://localhost:8000`
   - Set variable `token` = (leave empty, will be filled by tests)

3. **Run login test:**
   - Expand "Auth" folder
   - Click "Login"
   - Click "Send"
   - Copy token from response into `token` environment variable

4. **Run document tests:**
   - Try "List Documents"
   - Try "Create Document"
   - Verify responses

### Running Automated Tests

```bash
# From backend directory
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app

# Generate coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Troubleshooting Installation Issues

### Issue: "Cannot connect to database"

**Cause:** Database service not running or connection string wrong

**Solution:**
```bash
# Docker: Check if db container is running
docker-compose ps

# If not running:
docker-compose up -d db

# Check database logs
docker-compose logs db

# Linux: Restart PostgreSQL
sudo systemctl restart postgresql

# Windows: Check Services → PostgreSQL is running
```

### Issue: "Port 8000 already in use"

**Cause:** Another service using port 8000

**Solution:**
```bash
# Linux/Mac: Find process using port
lsof -i :8000
kill -9 <PID>

# Windows PowerShell:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port:
uvicorn app.main:app --port 8001
```

### Issue: "Module not found: app"

**Cause:** Virtual environment not activated or wrong directory

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Verify you're in backend directory
cd backend
ls -la app/  # Should show app directory

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "Alembic migration failed"

**Cause:** Database schema out of sync

**Solution:**
```bash
# Downgrade to base
alembic downgrade base

# Upgrade again
alembic upgrade head

# If still failing, reinitialize:
# (WARNING: This deletes all data!)
# 1. Drop database: dropdb q_docs_db
# 2. Create database: createdb q_docs_db
# 3. Run migrations: alembic upgrade head
```

### Issue: "Admin user not created"

**Cause:** Seed script didn't run

**Solution:**
```bash
# Run seed script manually
cd backend
python3 << 'EOF'
from app.database import Session
from app.models import User, Role
from app.core.security import get_password_hash

db = Session()
admin_role = db.query(Role).filter_by(name="DMS_ADMIN").first()
if admin_role and not db.query(User).filter_by(username="admin").first():
    admin = User(
        username="admin",
        email="admin@q-docs.local",
        hashed_password=get_password_hash("TempPassword@123456"),
        is_active=True,
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    print("Admin user created successfully")
else:
    print("User already exists or role not found")
EOF
```

### Issue: "Email notifications not sending"

**Cause:** SMTP credentials incorrect or service blocked

**Solution:**
```bash
# Test SMTP connection
python3 << 'EOF'
import smtplib
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("your-email@gmail.com", "your-app-password")
print("SMTP connection successful!")
EOF

# Check .env file for correct SMTP settings
# Verify firewall port 587 is open
# For Gmail: Use app-specific password, not main password
```

---

## Next Steps (Production Deployment)

### Before Going Live

- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY and JWT_SECRET_KEY
- [ ] Set `APP_DEBUG=false`
- [ ] Setup proper logging and monitoring
- [ ] Configure database backups
- [ ] Setup SSL/HTTPS certificate
- [ ] Configure firewall rules
- [ ] Setup load balancer (if multi-server)
- [ ] Configure email domain authentication (SPF, DKIM, DMARC)
- [ ] Create admin user accounts for team
- [ ] Create document templates for organization
- [ ] Test complete workflows end-to-end
- [ ] Setup monitoring and alerting
- [ ] Create runbooks and documentation

### Recommended Production Stack

```
┌─────────────────────────────────────┐
│         Frontend (React)             │
│       (Separate deployment)          │
└────────────────┬────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────┐
│      Nginx Reverse Proxy             │
│     (SSL Termination, Caching)       │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    Docker Container Orchestration    │
│  (Kubernetes or Docker Swarm)        │
└────────────────┬────────────────────┘
                 │
         ┌───────┼───────┐
         │       │       │
┌────────▼──┐ ┌──▼───────┴───┐
│  FastAPI  │ │  FastAPI (1) │
│Container  │ │  Container(N)│
└────────┬──┘ └──┬────────────┘
         │       │
         └───┬───┘
         ┌───▼────────────────┐
         │   PostgreSQL       │
         │ (Primary/Replica)  │
         └────────────────────┘
```

### Deployment Guides

- **Docker Swarm:** See `docs/DEPLOYMENT_DOCKER_SWARM.md`
- **Kubernetes:** See `docs/DEPLOYMENT_KUBERNETES.md`
- **AWS EC2:** See `docs/DEPLOYMENT_AWS.md`
- **Azure App Service:** See `docs/DEPLOYMENT_AZURE.md`

---

## Support & Documentation

- **API Documentation:** http://localhost:8000/api/docs
- **Installation Logs:** Check `backend/logs/` directory
- **Database Issues:** Review PostgreSQL logs
- **Performance:** See `docs/PERFORMANCE_TUNING.md`
- **Security:** See `docs/SECURITY_GUIDE.md`

---

**Installation Complete! Your Q-Docs system is ready.** 🎉

For questions, contact the DMS support team or refer to additional documentation in the `docs/` folder.

**Version:** 1.0.0 | **Last Updated:** February 2026
