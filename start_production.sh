#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================="
echo "Starting Pharma DMS Backend for Azure"
echo "=========================================="

# Run database migrations
echo "Applying database migrations..."
alembic upgrade head

# Initialize default admin and roles if not exists
echo "Initializing database seed data..."
python scripts/init_db.py

# Start Gunicorn server with Uvicorn worker
echo "Starting application server..."
# Azure App Service sets the PORT environment variable dynamically
PORT_NUMBER=${PORT:-8000}
exec gunicorn --forwarded-allow-ips="*" -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT_NUMBER app.main:app
