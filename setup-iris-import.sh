#!/bin/bash
# Setup script for IRIS Publications Import System

echo "=========================================="
echo "IRIS Publications Import - Setup Script"
echo "=========================================="
echo ""

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container..."
else
    echo "This script should be run inside the Docker container."
    echo "Run: docker-compose exec web bash setup-iris-import.sh"
    exit 1
fi

# Apply migrations
echo "1. Creating database migrations..."
python manage.py makemigrations main

echo ""
echo "2. Applying migrations..."
python manage.py migrate

echo ""
echo "3. Checking Celery configuration..."
python manage.py shell << EOF
from myproject.celery import app
print("Celery app:", app)
print("Beat schedule:", app.conf.beat_schedule)
EOF

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add staff members with IRIS IDs in Django admin (/admin/main/staff/)"
echo "2. Test manual import by clicking 'Import IRIS Publications' button"
echo "3. Check import logs in admin (/admin/main/irisimportlog/)"
echo ""
echo "To start Celery worker (if not already running):"
echo "  celery -A myproject worker -l info"
echo ""
echo "To start Celery beat (for scheduled tasks):"
echo "  celery -A myproject beat -l info"
echo ""
