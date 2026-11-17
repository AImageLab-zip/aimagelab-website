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

echo "⏰ Setting up IRIS profile photos schedule..."
python manage.py setup_iris_photos_sync

# Celery beat has no Persistent=true: a scheduled run whose minute passed
# while the host was off is skipped silently. Re-dispatch anything overdue.
# This is a no-op when the schedules ran normally, so an ordinary deploy
# does not trigger a full LDAP sync and photo import.
echo "⏰ Checking for schedules missed while the host was down..."
python manage.py run_missed_schedules || true

# Compile the stylesheet (Tailwind standalone CLI, no Node). Done here rather
# than at image build because the templates are bind-mounted at run time.
if [ -x "${TAILWIND_HOME:-/opt/tailwind}/tailwindcss" ]; then
    echo "🎨 Compiling CSS..."
    /app/frontend/build.sh
    if [ "$DEBUG" != "0" ]; then
        # Development: keep recompiling as templates change. --watch=always
        # keeps the watcher alive without a terminal attached.
        /app/frontend/build.sh --watch=always &
    fi
else
    echo "⚠️  Tailwind CLI not found in the image: rebuild it (css/app.css will be missing)"
fi

# Collect static files if needed (in production)
if [ "$DEBUG" = "0" ]; then
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Start the main process
echo "🎯 Starting application server..."
exec "$@"
