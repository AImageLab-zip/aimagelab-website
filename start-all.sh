#!/bin/bash
# Start both production and development environments

set -e

echo "🚀 Starting AImageLab - Full Stack (Production + Development)"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    exit 1
fi

# Build and start production
echo "Building and starting production services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build and start development
echo "Building and starting development services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Run migrations for both databases
echo "Running database migrations (Production)..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T django-app python manage.py migrate

echo "Running database migrations (Development)..."
docker-compose exec -T dev-django-app python manage.py migrate

# Collect static files for production
echo "Collecting static files..."
docker-compose exec -T django-app python manage.py collectstatic --noinput

echo ""
echo "✓ Full stack is ready!"
echo ""
echo "Access points:"
echo "  - Production:  https://aimagelab-app.ing.unimore.it (port 443)"
echo "  - Development: https://aimagelab-app.ing.unimore.it:8443"
echo "  - Direct dev:  http://localhost:8001"
echo ""
echo "Database ports:"
echo "  - Production MySQL:  localhost:3307"
echo "  - Development MySQL: localhost:3308"
echo "  - Production Redis:  localhost:6379"
echo "  - Development Redis: localhost:6380"
echo ""
echo "To create superusers:"
echo "  Production:  docker-compose exec django-app python manage.py createsuperuser"
echo "  Development: docker-compose exec dev-django-app python manage.py createsuperuser"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
