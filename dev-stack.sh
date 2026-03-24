#!/bin/bash

# Script to manage multiple isolated development stacks
# Usage: ./dev-stack.sh <stack-name> <command> [port]
#   stack-name: unique identifier for this dev stack (e.g., feature1, user1, etc.)
#   command: up, down, logs, ps, restart
#   port: apache host port (optional, defaults to auto-assign based on stack name)

set -e

STACK_NAME="${1:-default}"
COMMAND="${2:-up}"

if [ -z "$STACK_NAME" ]; then
    echo "Usage: $0 <stack-name> <command> [port]"
    echo "  stack-name: unique identifier (e.g., feature1, user1)"
    echo "  command: up, down, logs, ps, restart, exec, shell"
    echo "  port: custom Apache port (optional, auto-assigned if not provided)"
    echo ""
    echo "Examples:"
    echo "  $0 feature1 up           # Start stack 'feature1' with auto port"
    echo "  $0 feature1 up 8090      # Start stack 'feature1' on port 8090"
    echo "  $0 feature1 logs         # View logs for stack 'feature1'"
    echo "  $0 feature1 shell        # Open Django shell in stack 'feature1'"
    echo "  $0 feature1 down         # Stop and remove stack 'feature1'"
    exit 1
fi

# Generate project name
PROJECT_NAME="${STACK_NAME}"
ENV_FILE=".env.${PROJECT_NAME}"


# Always load base .env file first
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if custom env file exists and override with its values
if [ -f "${ENV_FILE}" ]; then
    echo "Using custom environment file: ${ENV_FILE}"
    export $(grep -v '^#' ${ENV_FILE} | xargs)
fi

echo "🚀 Development Stack: $STACK_NAME"
echo "📦 Project Name: $PROJECT_NAME"
echo "🌐 Apache Port: $DEV_APACHE_PORT"
echo ""

PORT=$DEV_APACHE_PORT

# Collect all DEV_ env vars to pass through sudo
SUDO_ENV=""
for var in $(compgen -v | grep '^DEV_\|^DB_\|^MYSQL_\|^SECRET_KEY\|^DEBUG\|^CELERY_\|^CACHE_\|^IRIS_\|^OIDC_\|^LDAP_\|^MAILINGLIST_\|^TZ'); do
    SUDO_ENV="$SUDO_ENV $var=${!var}"
done

case "$COMMAND" in
    up)
        echo "Starting development stack..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml up -d \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev
        echo ""
        echo "✅ Stack '$STACK_NAME' is running!"
        echo "   Access URL: http://localhost:$PORT"
        echo "   Django direct: http://localhost:$(sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml port dev-django-app 8000 2>/dev/null | cut -d: -f2 || echo "N/A")"
        echo ""
        echo "Useful commands:"
        echo "  View logs:    $0 $STACK_NAME logs"
        echo "  Django shell: $0 $STACK_NAME shell"
        echo "  Stop stack:   $0 $STACK_NAME down"
        ;;
    
    down)
        echo "Stopping and removing development stack..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml down
        echo "✅ Stack '$STACK_NAME' stopped and removed"
        ;;
    
    logs)
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml logs -f "${@:3}"
        ;;
    
    ps)
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml ps
        ;;
    
    restart)
        echo "Restarting development stack..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml restart "${@:3}"
        echo "✅ Stack '$STACK_NAME' restarted"
        ;;
    
    exec)
        if [ -z "$4" ]; then
            echo "Usage: $0 $STACK_NAME exec <service> <command>"
            echo "Example: $0 $STACK_NAME exec dev-django-app python manage.py migrate"
            exit 1
        fi
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml exec "${@:3}"
        ;;
    
    shell)
        echo "Opening Django shell for stack '$STACK_NAME'..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml exec dev-django-app python manage.py shell
        ;;
    
    migrate)
        echo "Running migrations for stack '$STACK_NAME'..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml exec dev-django-app python manage.py migrate
        ;;

    manage)
        echo "Running migrations for stack '$STACK_NAME'..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml exec dev-django-app python manage.py "${@:3}"
        ;;
    
    build)
        echo "Building development stack..."
        sudo $SUDO_ENV docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.dev.yml build \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev
        echo "✅ Stack '$STACK_NAME' built"
        ;;
    
    *)
        echo "Unknown command: $COMMAND"
        echo "Available commands: up, down, logs, ps, restart, exec, shell, migrate, build"
        exit 1
        ;;
esac
