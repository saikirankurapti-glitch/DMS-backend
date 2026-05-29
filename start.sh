#!/bin/bash

# Pharma DMS - Quick Start Script

echo "=========================================="
echo "Pharma DMS - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "=========================================="
    echo "✓ Services started successfully!"
    echo "=========================================="
    echo ""
    echo "Access the application at:"
    echo "  • API Documentation: http://localhost:8000/api/docs"
    echo "  • API: http://localhost:8000"
    echo "  • pgAdmin: http://localhost:5050"
    echo ""
    echo "Default Admin Credentials:"
    echo "  • Username: admin"
    echo "  • Password: Admin@123456"
    echo ""
    echo "⚠️  IMPORTANT: Change the admin password after first login!"
    echo ""
    echo "To view logs: docker-compose logs -f backend"
    echo "To stop services: docker-compose down"
    echo "=========================================="
else
    echo ""
    echo "❌ Failed to start services. Please check the logs:"
    echo "   docker-compose logs"
    exit 1
fi

