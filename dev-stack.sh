#!/bin/bash

# Script to manage multiple isolated development stacks
# Usage: ./dev-stack.sh <stack-name> <command> [port]
#   stack-name: unique identifier for this dev stack (e.g., feature1, user1, etc.)
#   command: up, down, logs, ps, restart
#   port: apache host port (optional, defaults to auto-assign based on stack name)

set -e

STACK_NAME="${1:-}"
COMMAND="${2:-up}"
KNOWN_COMMANDS="up down logs ps restart exec shell migrate manage build init"

usage() {
    echo "Usage: $0 <stack-name> [command] [args...]"
    echo "  stack-name: unique identifier (e.g., feature1, user1)"
    echo "  command:    $KNOWN_COMMANDS (default: up)"
    echo "  Ports are auto-assigned per stack in .env.<stack-name>; edit that file to change them."
    echo ""
    echo "Examples:"
    echo "  $0 feature1 up           # Start stack 'feature1'"
    echo "  $0 feature1 logs         # View logs for stack 'feature1'"
    echo "  $0 feature1 shell        # Open Django shell in stack 'feature1'"
    echo "  $0 feature1 down         # Stop and remove stack 'feature1'"
    exit 1
}

[ -n "$STACK_NAME" ] || usage

# The first argument is the stack NAME. Running `./dev-stack.sh restart` used
# to silently create and start a whole new stack called "restart".
for c in $KNOWN_COMMANDS; do
    if [ "$STACK_NAME" = "$c" ]; then
        echo "❌ '$STACK_NAME' is a command, not a stack name."
        echo "   Did you mean: $0 <stack-name> $STACK_NAME"
        exit 1
    fi
done

# Compose project names allow lowercase letters, digits, '-' and '_'.
if ! [[ "$STACK_NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
    echo "❌ Invalid stack name '$STACK_NAME': use lowercase letters, digits, '-' or '_'."
    exit 1
fi

if ! [[ " $KNOWN_COMMANDS " == *" $COMMAND "* ]]; then
    echo "❌ Unknown command: $COMMAND"
    usage
fi

# Generate project name
PROJECT_NAME="${STACK_NAME}"
ENV_FILE=".env.${PROJECT_NAME}"

# Auto-create env file with unique ports if it doesn't exist
if [ ! -f "${ENV_FILE}" ]; then
    # Derive a deterministic offset (0–99) from the stack name
    HASH=$(echo -n "$STACK_NAME" | cksum | awk '{print $1}')
    OFFSET=$((HASH % 100))
    cat > "${ENV_FILE}" <<EOF
# Dev stack configuration for ${STACK_NAME} (auto-generated)
DEV_APACHE_PORT=$((8100 + OFFSET))
DEV_REDIS_PORT=$((6400 + OFFSET))
DEV_MYSQL_PORT=$((3400 + OFFSET))
DEV_DJANGO_PORT=$((9000 + OFFSET))
DEV_DEBUGPY_PORT=$((5700 + OFFSET))
EOF
    echo "📝 Created ${ENV_FILE} with auto-assigned ports (offset ${OFFSET})"
fi

# Compose reads the env files itself (a later --env-file overrides an earlier
# one), so no secret is exported into this shell or passed to sudo as an
# argument. The old `sudo VAR=value ... docker compose` form put every secret
# on the command line, where `ps` and the sudo log exposed it to all users.
ENV_ARGS=()
[ -f .env ] && ENV_ARGS+=(--env-file .env)
ENV_ARGS+=(--env-file "${ENV_FILE}")
COMPOSE=(sudo docker compose -p "$PROJECT_NAME" "${ENV_ARGS[@]}" -f docker-compose.yml -f docker-compose.dev.yml)

# Read a single non-secret value for display only.
env_value() {
    grep -hE "^$1=" .env "${ENV_FILE}" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d "\"'"
}

PORT=$(env_value DEV_APACHE_PORT)

echo "🚀 Development Stack: $STACK_NAME"
echo "📦 Project Name: $PROJECT_NAME"
echo "🌐 Apache Port: $PORT (loopback only; tunnel with: ssh -L $PORT:127.0.0.1:$PORT <user>@aimagelab.unimore.it)"
echo ""

case "$COMMAND" in
    up)
        echo "Starting development stack..."
        "${COMPOSE[@]}" up -d \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev
        echo ""
        echo "✅ Stack '$STACK_NAME' is running!"
        echo "   Access URL: http://localhost:$PORT"
        echo "   Django direct: http://localhost:$("${COMPOSE[@]}" port dev-django-app 8000 2>/dev/null | cut -d: -f2 || echo "N/A")"
        echo ""
        echo "Useful commands:"
        echo "  View logs:    $0 $STACK_NAME logs"
        echo "  Django shell: $0 $STACK_NAME shell"
        echo "  Stop stack:   $0 $STACK_NAME down"
        ;;
    
    down)
        echo "Stopping and removing development stack..."
        "${COMPOSE[@]}" down
        echo "✅ Stack '$STACK_NAME' stopped and removed"
        ;;
    
    logs)
        "${COMPOSE[@]}" logs -f "${@:3}"
        ;;
    
    ps)
        "${COMPOSE[@]}" ps
        ;;
    
    restart)
        echo "Restarting development stack..."
        "${COMPOSE[@]}" restart "${@:3}"
        echo "✅ Stack '$STACK_NAME' restarted"
        ;;
    
    exec)
        if [ -z "$4" ]; then
            echo "Usage: $0 $STACK_NAME exec <service> <command>"
            echo "Example: $0 $STACK_NAME exec dev-django-app python manage.py migrate"
            exit 1
        fi
        "${COMPOSE[@]}" exec "${@:3}"
        ;;
    
    shell)
        echo "Opening Django shell for stack '$STACK_NAME'..."
        "${COMPOSE[@]}" exec dev-django-app python manage.py shell
        ;;
    
    migrate)
        echo "Running migrations for stack '$STACK_NAME'..."
        "${COMPOSE[@]}" exec dev-django-app python manage.py migrate
        ;;

    manage)
        echo "Running manage.py command for stack '$STACK_NAME'..."
        "${COMPOSE[@]}" exec dev-django-app python manage.py "${@:3}"
        ;;
    
    build)
        echo "Building development stack..."
        "${COMPOSE[@]}" build \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev
        echo "✅ Stack '$STACK_NAME' built"
        ;;

    init)
        echo "Initialising development stack '$STACK_NAME' (build → up → migrate → collectstatic)..."
        echo ""

        echo "📦 Building containers..."
        "${COMPOSE[@]}" build \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev

        echo "🚀 Starting services..."
        "${COMPOSE[@]}" up -d \
            dev-django-app dev-mysql-db dev-redis \
            dev-celery-worker dev-celery-beat apache-dev

        echo "⏳ Waiting for services to be ready..."
        sleep 10

        echo "🗄️  Running migrations..."
        "${COMPOSE[@]}" exec -T dev-django-app python manage.py migrate

        echo "📁 Collecting static files..."
        "${COMPOSE[@]}" exec -T dev-django-app python manage.py collectstatic --noinput

        echo "🔄 Restarting Apache..."
        "${COMPOSE[@]}" restart apache-dev

        echo ""
        echo "✅ Stack '$STACK_NAME' initialised!"
        echo "   Access URL: http://localhost:$PORT"
        echo ""
        echo "To create a superuser:"
        echo "  $0 $STACK_NAME manage createsuperuser"
        ;;
    
    *)
        echo "Unknown command: $COMMAND"
        echo "Available commands: up, down, logs, ps, restart, exec, shell, migrate, manage, build, init"
        exit 1
        ;;
esac
