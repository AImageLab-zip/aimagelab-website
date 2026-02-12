#!/bin/bash
# Production deployment script

set -e

echo "🚀 Deploying AImageLab Production Environment"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.example and configure it."
    exit 1
fi

# Verify DEBUG is set to 0
if grep -q "DEBUG=1" .env; then
    echo "⚠️  WARNING: DEBUG is set to 1 in .env file!"
    echo "For production, DEBUG should be 0."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build production containers
echo "Building Docker containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production services
echo "Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T django-app python manage.py migrate

# Collect static files
echo "Collecting static files..."
docker-compose exec -T django-app python manage.py collectstatic --noinput

echo ""
echo "✓ Production environment is ready!"
echo "  - Production: https://aimagelab-app.ing.unimore.it"
echo ""
echo "To create a superuser, run:"
echo "  docker-compose exec django-app python manage.py createsuperuser"
echo ""
echo "To obtain SSL certificates, run:"
echo "  docker-compose run --rm certbot"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f django-app"
