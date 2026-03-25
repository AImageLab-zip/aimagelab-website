#!/bin/bash
# Production deployment script
# Usage: ./deploy.sh <command>
#   init   - First-time production deployment (with env validation)
#   update - Pull latest changes and update running production

set -e

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

# ── helpers ──────────────────────────────────────────────────────────

usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  init     First-time production deployment (validates .env, builds everything)"
    echo "  update   Pull latest changes, rebuild, migrate, restart"
    echo ""
    exit 1
}

validate_env() {
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

    # Verify SECRET_KEY is not the default insecure key
    SK=$(grep '^SECRET_KEY=' .env | cut -d'=' -f2-)
    if [[ -z "$SK" || "$SK" == *"insecure"* || "$SK" == *"change"* || "$SK" == *"dev-secret"* || ${#SK} -lt 50 ]]; then
        echo "❌ Error: SECRET_KEY in .env is missing or insecure!"
        echo "Generate a strong key with:"
        echo "  python3 -c 'import secrets; print(secrets.token_urlsafe(64))'"
        exit 1
    fi
}

# ── commands ─────────────────────────────────────────────────────────

cmd_init() {
    echo "🚀 Deploying AImageLab Production Environment"
    echo ""

    validate_env

    echo "🔨 Building Docker containers..."
    $COMPOSE build

    echo "▶️  Starting services..."
    $COMPOSE up -d

    echo "⏳ Waiting for services to be ready..."
    sleep 15

    echo "🗄️  Running database migrations..."
    $COMPOSE exec -T django-app python manage.py migrate

    echo "📦 Collecting static files..."
    $COMPOSE exec -T django-app python manage.py collectstatic --noinput

    echo ""
    echo "✅ Production environment is ready!"
    echo "  https://aimagelab-app.ing.unimore.it"
    echo ""
    echo "To create a superuser, run:"
    echo "  $COMPOSE exec django-app python manage.py createsuperuser"
    echo ""
    echo "To obtain SSL certificates, run:"
    echo "  $COMPOSE run --rm certbot"
    echo ""
    echo "To view logs:"
    echo "  $COMPOSE logs -f django-app"
}

cmd_update() {
    echo "🔄 Updating AImageLab Production Environment"
    echo ""

    # Store current directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    echo "📥 Pulling latest changes from main branch..."
    git fetch origin
    git pull origin main

    echo ""
    echo "🔨 Rebuilding Docker containers..."
    $COMPOSE build django-app celery-worker celery-beat apache-prod

    echo ""
    echo "🔄 Restarting production services..."
    $COMPOSE up -d django-app mysql-db redis celery-worker celery-beat apache-prod

    echo "⏳ Waiting for services to be ready..."
    sleep 10

    echo ""
    echo "🗄️  Running database migrations..."
    $COMPOSE exec -T django-app python manage.py migrate

    echo ""
    echo "📂 Syncing media files from development environment..."
    sudo ./sync-media-files.sh

    echo ""
    echo "📦 Collecting static files..."
    $COMPOSE exec -T django-app python manage.py collectstatic --noinput

    echo ""
    echo "🔄 Restarting Apache to apply changes..."
    $COMPOSE restart apache-prod

    echo ""
    echo "✅ Production environment updated successfully!"
    echo "  https://aimagelab-app.ing.unimore.it"
    echo ""
    echo "To view logs:"
    echo "  $COMPOSE logs -f django-app"
    echo "  $COMPOSE logs -f apache-prod"
}

# ── main ─────────────────────────────────────────────────────────────

CMD="${1:-}"

case "$CMD" in
    init)   cmd_init ;;
    update) cmd_update ;;
    *)      usage ;;
esac
