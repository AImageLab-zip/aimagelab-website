# AImageLab Application - Quick Reference

## 🚀 Quick Start

```bash
cd /home/administrator/aimagelab
./start-all.sh
```

## 📋 URLs

| Environment | URL | Port |
|------------|-----|------|
| Production | https://aimagelab-app.ing.unimore.it | 443 |
| Development | https://aimagelab-app.ing.unimore.it:8443 | 8443 |
| Dev Direct | http://localhost:8001 | 8001 |

## 🎯 Key Commands

### Start Services
```bash
./start-all.sh                  # Start everything
./dev-stack.sh mystack init     # First-time dev setup (build + migrate + static)
./dev-stack.sh mystack up       # Start existing dev stack
./deploy.sh init                # First-time production deployment
./deploy.sh update              # Update running production
```

### Create Superuser
```bash
# Production
docker-compose exec django-app python manage.py createsuperuser

# Development
docker-compose exec dev-django-app python manage.py createsuperuser
```

### View Logs
```bash
docker-compose logs -f django-app      # Production
docker-compose logs -f dev-django-app  # Development
```

### Migrations
```bash
# Production
docker-compose exec django-app python manage.py makemigrations
docker-compose exec django-app python manage.py migrate

# Development
docker-compose exec dev-django-app python manage.py makemigrations
docker-compose exec dev-django-app python manage.py migrate
```

### Stop Everything
```bash
docker-compose down
```

## 🗄️ Database Access

| Database | Host | Port | Name | User |
|----------|------|------|------|------|
| Production | localhost | 3307 | aimagelab_db | aimagelab_user |
| Development | localhost | 3308 | aimagelab_db_dev | aimagelab_user |

## 🔧 Container Overview

### Production (Port 443)
- `django-app` - Django + Gunicorn
- `mysql-db` - MySQL 8.0
- `redis` - Redis cache
- `celery-worker` - Background tasks (2x)
- `celery-beat` - Task scheduler

### Development (Port 8443)
- `dev-django-app` - Django runserver
- `dev-mysql-db` - MySQL 8.0
- `dev-redis` - Redis cache
- `dev-celery-worker` - Background tasks (2x)
- `dev-celery-beat` - Task scheduler

### Shared
- `apache` - Web server with SSL
- `certbot` - SSL certificates

## 📁 Project Structure

```
aimagelab/
├── docker-compose.yml              # Unified compose file
├── docker-compose.dev.yml          # Dev-only (optional)
├── docker-compose.prod.yml         # Prod-only (optional)
├── start-all.sh                    # Start everything
├── dev-stack.sh                    # Dev stack management (init, up, down, etc.)
├── deploy.sh                       # Production deployment (init, update)
├── .env                            # Environment variables
├── Dockerfile.dev                  # Django dev container
├── Dockerfile.prod                 # Django prod container
├── Dockerfile.apache.dev           # Apache dev container
├── Dockerfile.apache.prod          # Apache prod container
├── Dockerfile.celery               # Celery worker
├── Dockerfile.beat                 # Celery beat
├── Dockerfile.certbot              # Certbot
├── apache-dev.conf                 # Apache dev config
├── apache-prod.conf                # Apache prod config
├── entrypoint.sh                   # Django entrypoint
├── wait-for-db.py                  # DB wait script
├── docker-site/                    # Django application
│   ├── manage.py
│   ├── requirements.txt
│   ├── myproject/                  # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── celery.py
│   └── main/                       # Main app
│       ├── views.py
│       ├── urls.py
│       ├── models.py
│       └── templates/
│           └── main/
│               ├── base.html       # Base template with navbar
│               ├── home.html       # Home page
│               ├── login.html      # Login with "Hello World"
│               └── dashboard.html  # User dashboard
├── certbot-scripts/                # SSL management
├── mysql-init/                     # DB initialization
└── shibboleth/                     # Shibboleth config (optional)
```

## 🎨 Application Features

✅ Navigation bar on all pages  
✅ Login page with "Hello World" message  
✅ User authentication  
✅ User dashboard  
✅ Admin panel at `/admin/`  
✅ Responsive design  
✅ Celery for async tasks  
✅ SSL/HTTPS support  
✅ Shibboleth authentication ready (optional)

## 🔐 First Time Setup Checklist

- [ ] Edit `.env` with production values
- [ ] Run `./start-all.sh`
- [ ] Create superuser for production
- [ ] Create superuser for development
- [ ] Obtain Let's Encrypt certificates: `docker-compose run --rm certbot`
- [ ] Restart Apache: `docker-compose restart apache`
- [ ] Test production: https://aimagelab-app.ing.unimore.it
- [ ] Test development: https://aimagelab-app.ing.unimore.it:8443

## 📚 Documentation

See `README.md` for complete documentation.
