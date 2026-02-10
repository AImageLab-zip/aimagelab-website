#!/bin/bash
set -e

echo "🚀 Starting Django application with database wait..."

# Wait for database to be ready
python3 /app/wait-for-db.py

# Run any pending migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Setup LDAP sync periodic task
echo "⏰ Setting up LDAP sync schedule..."
python manage.py setup_ldap_sync

# Collect static files if needed (in production)
if [ "$DEBUG" = "0" ]; then
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Start the main process
echo "🎯 Starting application server..."
exec "$@"
