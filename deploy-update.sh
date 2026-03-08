#!/bin/bash
# Update production deployment script
# Pulls changes from main branch, runs migrations, collects static files, and restarts containers

set -e

echo "🔄 Updating AImageLab Production Environment"
echo ""

# Store current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Pull latest changes from main branch
echo "📥 Pulling latest changes from main branch..."
git fetch origin
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to pull changes from repository"
    exit 1
fi

echo ""
echo "🔨 Rebuilding Docker containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build django-app celery-worker celery-beat apache-prod

echo ""
echo "🔄 Restarting production services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d django-app mysql-db redis celery-worker celery-beat apache-prod

# Wait for database to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🗄️  Running database migrations..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T django-app python manage.py migrate

echo ""
echo "📦 Collecting static files..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T django-app python manage.py collectstatic --noinput

echo ""
echo "🔄 Restarting Apache to apply changes..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart apache-prod

echo ""
echo "✅ Production environment updated successfully!"
echo ""
echo "🌐 Access: https://aimagelab-app.ing.unimore.it"
echo ""
echo "📊 To view logs:"
echo "  docker compose logs -f django-app"
echo "  docker compose logs -f apache-prod"
echo ""
