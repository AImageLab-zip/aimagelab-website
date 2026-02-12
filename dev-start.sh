#!/bin/bash
# Development startup script

set -e

# Get project name from argument or use default
PROJECT_NAME="${1:-aimagelab}"
ENV_FILE=".env.${PROJECT_NAME}"
COMPOSE_CMD="docker compose -p ${PROJECT_NAME}"

# Always load base .env file first
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if custom env file exists and override with its values
if [ -f "${ENV_FILE}" ]; then
    echo "Using custom environment file: ${ENV_FILE}"
    export $(grep -v '^#' ${ENV_FILE} | xargs)
fi

echo "🚀 Starting AImageLab Development Environment (${PROJECT_NAME})"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
    exit 1
fi

# Build development containers
echo "Building Docker containers..."
${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml build

# Start development services
echo "Starting services..."
${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running database migrations..."
${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml exec -T dev-django-app python manage.py migrate

# Collect static files
echo "Collecting static files..."
${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml exec -T dev-django-app python manage.py collectstatic --noinput

# Restart Apache to reload static files
echo "Restarting Apache..."
${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml restart apache-dev

# Check if we need to create superuser
echo ""
echo "✓ Development environment is ready!"
echo "  Project: ${PROJECT_NAME}"
echo "  - Apache (HTTP): http://localhost:${DEV_APACHE_PORT:-8080}"
echo "  - Django dev server: http://localhost:${DEV_DJANGO_PORT:-8001}"
echo ""
echo "To create a superuser, run:"
echo "  ${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml exec dev-django-app python manage.py createsuperuser"
echo ""
echo "To view logs:"
echo "  ${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml logs -f dev-django-app"
