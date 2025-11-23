# AImageLab Application

A Docker-based Django application with separate development and production environments running simultaneously on the same host.

## Architecture

The application uses a **Docker Compose** setup that supports both production and development stacks with **separate Apache containers** for complete environment isolation.

### Container Overview

**Production Stack (Ports 80/443)**
- **django-app**: Django + Gunicorn (internal port 8000, exposed on host 8000)
- **mysql-db**: MySQL 8.0 database (host port 3307)
- **redis**: Redis cache and Celery broker (host port 6379)
- **celery-worker**: 2 Celery worker replicas
- **celery-beat**: Celery beat scheduler
- **apache-prod**: Production Apache with HTTPS, Let's Encrypt, and Shibboleth support

**Development Stack (Configurable HTTP Port)**
- **dev-django-app**: Django runserver with debugpy (host ports 8001, 5678)
- **dev-mysql-db**: MySQL 8.0 dev database (host port 3308)
- **dev-redis**: Redis for development (host port 6380)
- **dev-celery-worker**: 2 Celery worker replicas
- **dev-celery-beat**: Celery beat scheduler
- **apache-dev**: Development Apache HTTP-only proxy (host port `${DEV_APACHE_PORT:-8080}`)

**Shared Infrastructure**
- **certbot-renew**: Automatic SSL certificate renewal service (checks every 12 hours)

## Quick Start

### Prerequisites

- Docker and Docker Compose v2
- Ports 80, 443 available for production (apache-prod)
- Port 8080 (or custom `DEV_APACHE_PORT`) available for development (apache-dev)

### Option 1: Start Everything (Both Environments)

```bash
# Start production stack
sudo docker compose up -d django-app mysql-db redis celery-worker celery-beat apache-prod

# Start development stack
sudo docker compose up -d dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev

# Optional: Start certificate renewal service
sudo docker compose up -d certbot-renew
```

### Option 2: Start Development Stack

**Single development stack:**
```bash
# Start
sudo docker compose up -d dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev

# Stop
sudo docker compose down dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev
```

**Multiple isolated development stacks** (recommended):
```bash
# Start stack with auto-assigned port
./dev-stack.sh feature1 up

# Start stack on specific port
./dev-stack.sh feature2 up 8090

# Start another stack
./dev-stack.sh user1 up 8091

# Stop specific stack
./dev-stack.sh feature1 down
./dev-stack.sh feature2 down
```

### Option 3: Start Only Production

```bash
sudo docker compose up -d django-app mysql-db redis celery-worker celery-beat apache-prod certbot-renew
```

## Access URLs

- **Production (HTTPS)**: https://aimagelab-app.ing.unimore.it
- **Production (HTTP - redirects to HTTPS)**: http://aimagelab-app.ing.unimore.it
- **Development**: http://localhost:8080 (or http://localhost:${DEV_APACHE_PORT})
- **Dev Direct Access**: http://localhost:8001 (bypasses Apache, includes Django debug toolbar)
- **Dev Debugger**: Port 5678 (VS Code debugpy)

## Detailed Setup Instructions

## Detailed Setup Instructions

### 1. Environment Configuration

Copy the example environment file and configure it:

```bash
cd aimagelab
cp .env.example .env
```

Edit `.env` and update the values:
- Set a strong `SECRET_KEY` for production
- Update database passwords
- Configure your email for certbot
- Set `DEBUG=0` for production use

### 2. First Time Setup

**Build and start the production stack:**

```bash
sudo docker compose build django-app mysql-db redis celery-worker celery-beat apache-prod
sudo docker compose up -d django-app mysql-db redis celery-worker celery-beat apache-prod
```

**Build and start the development stack:**

```bash
sudo docker compose build dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev
sudo docker compose up -d dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev
```

This will:
- Build all Docker containers
- Start the selected environment(s)
- Run database migrations automatically
- Collect static files (production only)

**Create superuser accounts:**

```bash
# For production
sudo docker compose exec django-app python manage.py createsuperuser

# For development
sudo docker compose exec dev-django-app python manage.py createsuperuser
```

### 3. SSL Certificates

**Production (apache-prod):**

The `apache-prod` container automatically:
1. Creates self-signed certificates on first start if none exist
2. Starts Apache with self-signed certificates
3. Attempts to obtain Let's Encrypt certificates via ACME challenge
4. Reloads Apache with Let's Encrypt certificates if successful
5. Falls back to self-signed certificates if Let's Encrypt fails

The `certbot-renew` service automatically checks for certificate renewal every 12 hours.

**Development (apache-dev):**

Development uses HTTP only - no certificates required.

## Common Operations

## Common Operations

### Managing Services

**View running containers:**
```bash
sudo docker compose ps
```

**View logs:**
```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f django-app
sudo docker compose logs -f dev-django-app
sudo docker compose logs -f apache-prod
sudo docker compose logs -f apache-dev
```

**Restart services:**
```bash
# Restart all
sudo docker compose restart

# Restart specific service
sudo docker compose restart django-app
sudo docker compose restart apache-prod
sudo docker compose restart apache-dev
```

**Stop services:**
```bash
# Stop all
sudo docker compose down

# Stop only production
sudo docker compose stop django-app mysql-db redis celery-worker celery-beat apache-prod certbot-renew

# Stop only development
sudo docker compose stop dev-django-app dev-mysql-db dev-redis dev-celery-worker dev-celery-beat apache-dev
```

### Environment Configuration

The development Apache port can be customized in `.env`:

```bash
# Set custom development port (default: 8080)
DEV_APACHE_PORT=8000
```

This allows running multiple development stacks on the same host by changing the port for each stack.

### Running Migrations

```bash
# Production
sudo docker compose exec django-app python manage.py makemigrations
sudo docker compose exec django-app python manage.py migrate

# Development
sudo docker compose exec dev-django-app python manage.py makemigrations
sudo docker compose exec dev-django-app python manage.py migrate
```

### Collecting Static Files

```bash
# Production
sudo docker compose exec django-app python manage.py collectstatic --noinput
```

### Accessing Django Shell

```bash
# Production
sudo docker compose exec django-app python manage.py shell

# Development
sudo docker compose exec dev-django-app python manage.py shell
```

### Database Access

```bash
# Production MySQL
mysql -h 127.0.0.1 -P 3307 -u aimagelab_user -p aimagelab_db

# Development MySQL
mysql -h 127.0.0.1 -P 3308 -u aimagelab_user -p aimagelab_db_dev

# Or via Docker
sudo docker compose exec mysql-db mysql -u aimagelab_user -p aimagelab_db
sudo docker compose exec dev-mysql-db mysql -u aimagelab_user -p aimagelab_db_dev
```

## Application Features

- **Navigation Bar**: Responsive navigation on all pages with dynamic login/logout
- **Login Page**: Custom login page with "Hello World" greeting
- **User Authentication**: Django's built-in authentication system
- **Dashboard**: User dashboard accessible after login
- **Admin Panel**: Django admin interface at `/admin/`
- **Responsive Design**: Mobile-friendly templates

## Celery Tasks

Celery is configured for async task processing. Create tasks in `docker-site/main/tasks.py`:

```python
from celery import shared_task

@shared_task
def my_background_task(arg1, arg2):
    # Your task code here
    return result
```

Use tasks in your views:

```python
from .tasks import my_background_task

# In your view
my_background_task.delay(value1, value2)
```

## Database Backups

**Export (backup):**
```bash
# Production
sudo docker compose exec mysql-db mysqldump -u aimagelab_user -p aimagelab_db > backup_prod_$(date +%Y%m%d).sql

# Development
sudo docker compose exec dev-mysql-db mysqldump -u aimagelab_user -p aimagelab_db_dev > backup_dev_$(date +%Y%m%d).sql
```

**Import (restore):**
```bash
# Production
sudo docker compose exec -T mysql-db mysql -u aimagelab_user -p aimagelab_db < backup_prod_20250101.sql

# Development
sudo docker compose exec -T dev-mysql-db mysql -u aimagelab_user -p aimagelab_db_dev < backup_dev_20250101.sql
```

## Key Differences: Production vs Development

| Feature | Production (`apache-prod`) | Development (`apache-dev`) |
|---------|---------------------------|---------------------------|
| **Protocol** | HTTPS (ports 80→443) | HTTP only |
| **SSL/TLS** | Let's Encrypt certificates | None |
| **Host Port** | 80, 443 (fixed) | `${DEV_APACHE_PORT:-8080}` (configurable) |
| **Shibboleth** | Enabled (if configured) | Disabled |
| **Django Server** | Gunicorn (production WSGI) | runserver (auto-reload) |
| **Static Files** | Served by Apache | Served by Django |
| **Debug Mode** | `DEBUG=0` | `DEBUG=1` |
| **Database** | `aimagelab_db` (port 3307) | `aimagelab_db_dev` (port 3308) |
| **Redis** | Port 6379 | Port 6380 |
| **Multiple Instances** | Single production instance | Multiple dev stacks via `dev-stack.sh` |

## Managing Multiple Development Stacks

The `dev-stack.sh` script allows you to run multiple isolated development environments simultaneously:

**Start a new stack:**
```bash
./dev-stack.sh myfeature up          # Auto-assigns port
./dev-stack.sh myfeature up 8090     # Use specific port 8090
```

**Common operations:**
```bash
# View logs
./dev-stack.sh myfeature logs

# Django shell
./dev-stack.sh myfeature shell

# Run migrations
./dev-stack.sh myfeature migrate

# Execute custom command
./dev-stack.sh myfeature exec dev-django-app python manage.py createsuperuser

# Check running containers
./dev-stack.sh myfeature ps

# Restart services
./dev-stack.sh myfeature restart

# Stop and remove stack
./dev-stack.sh myfeature down
```

**List all your dev stacks:**
```bash
sudo docker ps --filter "name=aimagelab-dev-"
```

Each stack gets:
- Unique container names (`aimagelab-dev-myfeature-*`)
- Isolated database and Redis instances
- Separate volumes
- Independent Apache port

## Technologies Used

- **Django 4.2+**: Web framework
- **Gunicorn**: WSGI server (production)
- **MySQL 8.0**: Database
- **Redis**: Cache and message broker
- **Celery**: Async task processing
- **Apache**: Web server with mod_shib
- **Shibboleth**: Authentication (optional)
- **Let's Encrypt**: SSL certificates
- **Docker**: Containerization

## Security Notes

- Change all default passwords in production
- Use strong `SECRET_KEY`
- Set `DEBUG=0` in production
- Configure firewall rules
- Keep SSL certificates up to date
- Regular security updates for all containers

## Support

For issues or questions, contact the development team.
