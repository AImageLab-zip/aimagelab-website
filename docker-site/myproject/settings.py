"""
Django settings for myproject project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "1") == "1"

if not DEBUG and ("insecure" in SECRET_KEY or "change" in SECRET_KEY or len(SECRET_KEY) < 50):
    raise RuntimeError(
        "SECRET_KEY is insecure for production! "
        "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )

# Allow requests from the specified domain and localhost
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "aimagelab.unimore.it",  # Canonical domain
    "aimagelab-app.ing.unimore.it",
    "aimagelab.ing.unimore.it",
    # All supported aliases
    "imagelab.ing.unimo.it",
    "www.imagelab.unimo.it",
    "www.imagelab.ing.unimo.it",
    "imagelab.unimo.it",
    "www.aimagelab.unimo.it",
    "www.aimagelab.ing.unimo.it",
    "aimagelab.unimo.it",
    "aimagelab.ing.unimo.it",
    "0.0.0.0",
    "django-app",
    "dev-django-app",
    "testserver",
]

# CSRF trusted origins for cross-site requests
CSRF_TRUSTED_ORIGINS = [
    "https://aimagelab.unimore.it",  # Canonical domain
    "https://aimagelab-app.ing.unimore.it",
    "https://aimagelab-app.ing.unimore.it:8443",
    "https://aimagelab.ing.unimore.it",
    # All supported aliases
    "https://imagelab.ing.unimo.it",
    "https://www.imagelab.unimo.it",
    "https://www.imagelab.ing.unimo.it",
    "https://imagelab.unimo.it",
    "https://www.aimagelab.unimo.it",
    "https://www.aimagelab.ing.unimo.it",
    "https://aimagelab.unimo.it",
    "https://aimagelab.ing.unimo.it",
    # Development origins
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://aimagelab-app.ing.unimore.it:8000",
    "http://aimagelab-app.ing.unimore.it:8001",
    "http://aimagelab-app.ing.unimore.it:8002",
    "http://aimagelab-app.ing.unimore.it:8003",
    "http://aimagelab-app.ing.unimore.it:8080",
    "http://aimagelab-app.ing.unimore.it:8081",
    "http://aimagelab-app.ing.unimore.it:8082",
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
    "main.apps.MainConfig",
    "mailinglist.apps.MailinglistConfig",
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
    'markdownify.apps.MarkdownifyConfig',
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

# Cache Configuration (for IRIS import locking and other caching)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get("CACHE_URL", "redis://redis:6379/1"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# IRIS Gateway REST API Configuration
IRIS_API_BASE_URL = os.environ.get(
    "IRIS_API_BASE_URL", "https://iris.unimore.it/gw/rest/api"
)
IRIS_API_USERNAME = os.environ.get("IRIS_API_USERNAME", "")
IRIS_API_PASSWORD = os.environ.get("IRIS_API_PASSWORD", "")

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
LDAP_ATTRIBUTES = ['uid', 'givenName', 'sn', 'mail', 'employeeNumber']
    
# Role mapping from LDAP organizational units to Django UserProfile roles
LDAP_ROLE_MAPPING = {
    'rector': 'rector',
    'professori_ordinari': 'full_professor',
    'professori_associati': 'assoc_professor',
    'ricercatori_rtt': 'researcher_tt',
    'ricercatori_rtda': 'researcher_a',
    'ricercatori_rtdb': 'researcher_b',
    'personale_segreteria': 'secretariat_staff',
    'assegnisti': 'research_fellow',
    'collaborazioni': 'collaborator',
    'contratti_ricerca': 'research_fellow',
    'incarichi_ricerca': 'research_fellow',
    'incarichi_postdoc': 'postdoc',
    'dottorandi': 'phd',
    'past_members': 'past_member',
}

# Role priority (higher number = higher priority when user in multiple groups)
LDAP_ROLE_PRIORITY = {
    'rector': 99,
    'full_professor': 20,
    'assoc_professor': 19,
    'researcher_tt': 15,
    'researcher_b': 14,
    'researcher_a': 13,
    'postdoc': 10,
    'secretariat_staff': 5,
    'phd': 6,
    'research_fellow': 4,
    'research_contract': 4,
    'research_assignment': 4,
    'collaborator': 3,

    'alumni': 0,
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

# Markdownify Configuration
# Allow images and other HTML tags in markdown rendering
MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em', 
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 
            'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
        ],
        "WHITELIST_ATTRS": [
            'href', 'src', 'alt', 'title', 'class', 'id'
        ],
        "MARKDOWN_EXTENSIONS": [
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
        ],
    }
}

# ============================================================================
# Mailing List Configuration
# ============================================================================

# Gmail IMAP / SMTP credentials
MAILINGLIST_EMAIL_ADDRESS = os.environ.get('MAILINGLIST_EMAIL_ADDRESS', '')
MAILINGLIST_EMAIL_PASSWORD = os.environ.get('MAILINGLIST_EMAIL_PASSWORD', '')

# IMAP settings (for fetching incoming mail)
MAILINGLIST_IMAP_HOST = os.environ.get('MAILINGLIST_IMAP_HOST', 'imap.gmail.com')
MAILINGLIST_IMAP_PORT = int(os.environ.get('MAILINGLIST_IMAP_PORT', '993'))

# SMTP settings (for sending outgoing mail)
MAILINGLIST_SMTP_HOST = os.environ.get('MAILINGLIST_SMTP_HOST', 'smtp.gmail.com')
MAILINGLIST_SMTP_PORT = int(os.environ.get('MAILINGLIST_SMTP_PORT', '587'))

# Display name used in the From header of outgoing emails
MAILINGLIST_FROM_NAME = os.environ.get('MAILINGLIST_FROM_NAME', 'AImageLab Mailing List')

# Base URL for unsubscribe and moderation links
MAILINGLIST_BASE_URL = os.environ.get('MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')

# Sender domains that are auto-approved (no moderation needed)
# Comma-separated in the env var, e.g. "unimore.it,example.com"
_trusted = os.environ.get('MAILINGLIST_TRUSTED_DOMAINS', 'unimore.it')
MAILINGLIST_TRUSTED_DOMAINS = [d.strip() for d in _trusted.split(',') if d.strip()]

# Number of emails to send per batch (progressive sending)
MAILINGLIST_BATCH_SIZE = int(os.environ.get('MAILINGLIST_BATCH_SIZE', '20'))
