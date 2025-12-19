"""
Django settings for myproject project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-change-this-in-production"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "1") == "1"

# Allow requests from the specified domain and localhost
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "aimagelab-app.ing.unimore.it",
    "0.0.0.0",
    "django-app",
    "dev-django-app",
    "testserver",
]

# CSRF trusted origins for cross-site requests
CSRF_TRUSTED_ORIGINS = [
    "https://aimagelab-app.ing.unimore.it",
    "https://aimagelab-app.ing.unimore.it:8443",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Security settings for proxy setup
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_TZ = True

# Session and CSRF settings for HTTPS
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_celery_beat",
    "phonenumber_field",
    "mozilla_django_oidc",  # OIDC authentication
    "main.apps.MainConfig",
    "django_sass", #https://pypi.org/project/django-sass/
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",  # OIDC session refresh
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "aimagelab_db"),
        "USER": os.environ.get("DB_USER", "aimagelab_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "aimagelab_pass123"),
        "HOST": os.environ.get("DB_HOST", "mysql-db"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TZ", "Europe/Rome")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery Configuration
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Scheduler - Use database-backed scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# LDAP Sync Schedule Configuration
# Time when the daily LDAP sync should run (24-hour format)
LDAP_SYNC_HOUR = int(os.environ.get("LDAP_SYNC_HOUR", "2"))  # Default: 2 AM
LDAP_SYNC_MINUTE = int(os.environ.get("LDAP_SYNC_MINUTE", "0"))  # Default: 00 minutes

# LDAP Configuration
LDAP_SERVER_URI = 'ldap://ailb-login-01.ing.unimore.it:389'
LDAP_SEARCH_BASE = 'dc=aimagelab,dc=unimore,dc=it'
LDAP_BIND_DN = None  # Anonymous bind
LDAP_BIND_PASSWORD = None
LDAP_ATTRIBUTES = ['uid', 'givenName', 'sn', 'mail']

# Role mapping from LDAP organizational units to Django UserProfile roles
LDAP_ROLE_MAPPING = {
    'strutturati': 'professor', #provvisorio
    'dottorandi': 'phd',
    'tesisti': 'intern',
    'studenti': 'alumni',
    'past_members': 'past_member',
    'ospiti': 'alumni',
}

# Role priority (higher number = higher priority when user in multiple groups)
LDAP_ROLE_PRIORITY = {
    'professor': 5,
    'postdoc': 4,
    'phd': 3,
    'intern': 2,
    'alumni': 1,
    'past_member': 0,
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ============================================================================
# OIDC (OpenID Connect) Configuration
# ============================================================================

# Authentication backends - support both OIDC and traditional Django auth
AUTHENTICATION_BACKENDS = [
    'main.oidc_backend.CustomOIDCAuthenticationBackend',  # Custom OIDC backend
    'django.contrib.auth.backends.ModelBackend',  # Traditional username/password
]

# OIDC Relying Party (RP) Settings - Your application credentials
OIDC_RP_CLIENT_ID = os.environ.get('OIDC_RP_CLIENT_ID', 'your-client-id-here')
OIDC_RP_CLIENT_SECRET = os.environ.get('OIDC_RP_CLIENT_SECRET', 'your-client-secret-here')

# OIDC Provider (OP) Endpoints - Your OIDC provider URLs
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get(
    'OIDC_OP_AUTHORIZATION_ENDPOINT',
    'https://your-oidc-provider.com/oauth2/authorize'
)
OIDC_OP_TOKEN_ENDPOINT = os.environ.get(
    'OIDC_OP_TOKEN_ENDPOINT',
    'https://your-oidc-provider.com/oauth2/token'
)
OIDC_OP_USER_ENDPOINT = os.environ.get(
    'OIDC_OP_USER_ENDPOINT',
    'https://your-oidc-provider.com/oauth2/userinfo'
)
OIDC_OP_JWKS_ENDPOINT = os.environ.get(
    'OIDC_OP_JWKS_ENDPOINT',
    'https://your-oidc-provider.com/oauth2/jwks'
)

# Optional: Logout endpoint
OIDC_OP_LOGOUT_ENDPOINT = os.environ.get(
    'OIDC_OP_LOGOUT_ENDPOINT',
    'https://your-oidc-provider.com/oauth2/logout'
)

# OIDC Scopes - Information to request from the provider
OIDC_RP_SCOPES = os.environ.get('OIDC_RP_SCOPES', 'openid email profile')

# Algorithm used to sign ID tokens
OIDC_RP_SIGN_ALGO = os.environ.get('OIDC_RP_SIGN_ALGO', 'RS256')

# Redirect URIs after authentication
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# OIDC-specific login/logout redirect URLs
OIDC_AUTHENTICATION_CALLBACK_URL = 'oidc_authentication_callback'
OIDC_OP_LOGOUT_URL_METHOD = 'main.oidc_backend.provider_logout'

# Session configuration for OIDC
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 3600  # Renew token every hour

# Optional: Custom claim mappings
# Map OIDC claims to Django user fields
OIDC_USERNAME_ALGO = 'main.oidc_backend.generate_username'

# Create user if not exists when authenticating via OIDC
OIDC_CREATE_USER = True

# Use nonce for security
OIDC_USE_NONCE = True

# Store ID token (useful for logout)
OIDC_STORE_ID_TOKEN = True

# Default role for new OIDC users
OIDC_DEFAULT_USER_ROLE = os.environ.get('OIDC_DEFAULT_USER_ROLE', 'phd')

# Provider display name (for UI)
OIDC_PROVIDER_NAME = os.environ.get('OIDC_PROVIDER_NAME', 'OIDC Provider')
