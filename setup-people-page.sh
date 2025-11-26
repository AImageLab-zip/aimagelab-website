#!/bin/bash
# Quick setup script for People page feature

set -e

echo "🚀 Setting up People page feature..."
echo ""

cd /home/administrator/aimagelab

echo "📦 Installing Pillow for image support..."
sudo docker compose exec dev-django-app pip install Pillow>=10.0.0

echo ""
echo "🗄️  Creating migrations..."
sudo docker compose exec dev-django-app python manage.py makemigrations

echo ""
echo "⬆️  Running migrations..."
sudo docker compose exec dev-django-app python manage.py migrate

echo ""
echo "👥 Populating database with fake team members..."
sudo docker compose exec dev-django-app python manage.py populate_team

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Visit the People page at: http://localhost:8080/people/"
echo ""
