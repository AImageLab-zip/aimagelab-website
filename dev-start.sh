#!/bin/bash
# Development startup script

set -e

echo "🚀 Starting AImageLab Development Environment"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    exit 1
fi

# Build development containers
echo "Building Docker containers..."
docker-compose build dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev

# Start development services
echo "Starting services..."
docker-compose up -d dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose exec -T dev-django-app python manage.py migrate

# Check if we need to create superuser
echo ""
echo "✓ Development environment is ready!"
echo "  - Development: https://aimagelab-app.ing.unimore.it:8443"
echo "  - Django dev server: http://localhost:8001"
echo ""
echo "To create a superuser, run:"
echo "  docker-compose exec dev-django-app python manage.py createsuperuser"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f dev-django-app"
