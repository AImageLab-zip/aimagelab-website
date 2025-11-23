# AImageLab Architecture Diagram

## System Overview

```
                                                   INTERNET
                                                         |
                               ┌─────────────────┴─────────────────┐
                               |                                   |
                        Port 80 (HTTP)                      Port 443 (HTTPS)
                               |                                   |
                               └───────────────┬───────────────────┘
                                                       ▼
                                ╔════════════════════════════╗
                                ║       apache-prod          ║
                                ║  - HTTP→HTTPS redirect     ║
                                ║  - Shibboleth + TLS        ║
                                ║  - Let's Encrypt certs     ║
                                ╚════════════════════════════╝
                                                       |
                                                       ▼
                                ╔════════════════════════════╗
                                ║      Production Stack      ║
                                ╚════════════════════════════╝


 Developer Laptop (browser, Postman, etc.)
                              |
 Host port ${DEV_APACHE_PORT:-8080} (HTTP)
                              ▼
             ╔════════════════════════════╗
             ║        apache-dev          ║
             ║  - HTTP reverse proxy      ║
             ║  - Configurable host port  ║
             ╚════════════════════════════╝
                              |
                              ▼
             ╔════════════════════════════╗
             ║      Development Stack     ║
             ╚════════════════════════════╝
```

## Production Stack (Port 443)

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Network                        │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ django-app   │────────▶│  mysql-db    │                  │
│  │ (Gunicorn)   │         │  (MySQL 8.0) │                  │
│  │ Port: 8000   │         │  Port: 3306  │                  │
│  │              │         │  Host: 3307  │                  │
│  └──────┬───────┘         └──────────────┘                  │
│         │                                                     │
│         │                                                     │
│         │                 ┌──────────────┐                  │
│         └────────────────▶│    redis     │                  │
│                           │  Port: 6379  │                  │
│                           │  (Broker)    │                  │
│                           └──────┬───────┘                  │
│                                  │                           │
│                    ┌─────────────┴──────────────┐           │
│                    │                             │           │
│            ┌───────▼────────┐          ┌────────▼───────┐  │
│            │ celery-worker  │          │ celery-beat    │  │
│            │ (2 replicas)   │          │ (scheduler)    │  │
│            └────────────────┘          └────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```
      
## Development Stack (Configurable HTTP Port)

```
┌─────────────────────────────────────────────────────────────┐
│                   Development Network                        │
│                                                               │
│  ┌──────────────┐         ┌──────────────────┐              │
│  │dev-django-app│────────▶│ dev-mysql-db     │              │
│  │ (runserver)  │         │  (MySQL 8.0)     │              │
│  │ Port: 8000   │         │  Port: 3306      │              │
│  │ Host: 8001   │         │  Host: 3308      │              │
│  │ Debug: 5678  │         └──────────────────┘              │
│  └──────┬───────┘                                            │
│         │                                                     │
│         │                 ┌──────────────┐                  │
│         └────────────────▶│  dev-redis   │                  │
│                           │  Port: 6379  │                  │
│                           │  Host: 6380  │                  │
│                           └──────┬───────┘                  │
│                                  │                           │
│                    ┌─────────────┴──────────────┐           │
│                    │                             │           │
│        ┌───────────▼──────────┐      ┌─────────▼────────┐  │
│        │ dev-celery-worker    │      │ dev-celery-beat  │  │
│        │ (2 replicas)         │      │ (scheduler)      │  │
│        └──────────────────────┘      └──────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Shared Services

```
┌─────────────────────────────────────────────────────────────┐
│                      Shared Network                          │
│                                                               │
│  ┌──────────────┐              ┌──────────────┐             │
│  │ apache-prod  │◀─────────────│   certbot    │             │
│  │ Ports: 80/443│  SSL Certs   │ Let's Encrypt│             │
│  │ TLS + Shib   │              └──────────────┘             │
│  └───────┬──────┘                                            │
│          │                                                   │
│  ┌───────▼──────┐                                           │
│  │ apache-dev   │                                           │
│  │ Port: 80     │◀─ Host ${DEV_APACHE_PORT:-8080}           │
│  │ HTTP proxy   │                                           │
│  └──────────────┘                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow

### Production Request (Port 80/443)

```
User Browser
     │
     │ HTTPS (443)
     ▼
┌─────────────┐
│   Apache    │
│  Port 443   │
└─────┬───────┘
      │
      │ ProxyPass
      ▼
┌─────────────┐       ┌──────────┐
│ django-app  │──────▶│ mysql-db │
│ (Gunicorn)  │       └──────────┘
│ Port 8000   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   redis     │
│ (Celery)    │
└─────────────┘
```

### Development Request (Host ${DEV_APACHE_PORT:-8080})

```
Developer Browser
     │
     │ HTTP (${DEV_APACHE_PORT:-8080})
     ▼
┌─────────────┐
│ apache-dev  │
│  Port 80    │
└─────┬───────┘
      │
      │ ProxyPass
      ▼
┌──────────────┐      ┌───────────────┐
│dev-django-app│─────▶│ dev-mysql-db  │
│ (runserver)  │      └───────────────┘
│ Port 8000    │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│  dev-redis   │
│  (Celery)    │
└──────────────┘
```

## Volume Mapping

```
Production:
      - mysql_data        → /var/lib/mysql (mysql-db)
      - redis_data        → /data (redis)
      - static_volume     → /app/static (django-app)
      - media_volume      → /app/media (django-app)
      - letsencrypt_data  → /etc/letsencrypt (apache-prod)
      - letsencrypt_webroot → /var/www/html/.well-known/acme-challenge (apache-prod, certbot)

Development:
      - dev_mysql_data    → /var/lib/mysql (dev-mysql-db)
      - dev_redis_data    → /data (dev-redis)
      - dev_static_volume → /var/www/html/static-dev (apache-dev) and /app/static (dev-django-app)
```

## Network Topology

```
┌──────────────────────────────────────────────────────┐
│                  Host Machine                         │
│                                                       │
│  ┌────────────────┐  ┌────────────────┐             │
│  │ prod-network   │  │ dev-network    │             │
│  │  - mysql-db    │  │  - dev-mysql-db│             │
│  │  - redis       │  │  - dev-redis   │             │
│  │  - django-app  │  │  - dev-django  │             │
│  │  - celery-*    │  │  - dev-celery* │             │
│  └────────┬───────┘  └────────┬───────┘             │
│           │                   │                       │
│           └─────────┬─────────┘                       │
│                     │                                 │
│           ┌─────────▼─────────┐                       │
│           │  shared-network   │                       │
│           │  - apache-prod    │                       │
│           │  - apache-dev     │                       │
│           │  - django-app     │                       │
│           │  - dev-django-app │                       │
│           │  - certbot        │                       │
│           └───────────────────┘                       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Port Mappings

| Service | Container Port | Host Port | Description |
|---------|----------------|-----------|-------------|
| apache-prod | 80 | 80 | Public HTTP (redirects to HTTPS) |
| apache-prod | 443 | 443 | Public HTTPS (production) |
| apache-dev | 80 | `${DEV_APACHE_PORT:-8080}` | Development HTTP proxy |
| django-app | 8000 | - | Production Django (internal) |
| dev-django-app | 8000 | 8001 | Development Django direct access |
| dev-django-app | 5678 | 5678 | VS Code debugpy |
| mysql-db | 3306 | 3307 | Production MySQL |
| dev-mysql-db | 3306 | 3308 | Development MySQL |
| redis | 6379 | 6379 | Production Redis |
| dev-redis | 6379 | 6380 | Development Redis |

## Environment Isolation

- **Production** and **Development** use separate databases
- **Production** and **Development** use separate Redis instances
- **Production** uses Gunicorn (production WSGI server)
- **Development** uses Django runserver (auto-reload, debug)
- Separate Apache containers: `apache-prod` (HTTPS with Let's Encrypt + Shibboleth) and `apache-dev` (HTTP-only)
- `DEV_APACHE_PORT` controls the host port for `apache-dev`, enabling multiple dev stacks on the same host
- SSL certificates live exclusively with `apache-prod` and Certbot; development traffic uses plain HTTP
