"""
Live Production Settings for DripEmails.org

This file contains production settings for the live site.
Use this configuration for the production environment.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required for production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True # enabled for now

ALLOWED_HOSTS = [
    'dripemails.org',
    'www.dripemails.org',
    'api.dripemails.org',
    'docs.dripemails.org',
    'localhost',
    '127.0.0.1',
    '127.0.0.1:8005',
    '0.0.0.0',
    '0.0.0.0:8005',
    '10.124.0.8',
    '10.124.0.8:8005',
    '*'
]

CSRF_TRUSTED_ORIGINS = [
    'https://dripemails.org',
    'https://www.dripemails.org',
    'https://api.dripemails.org',
    'https://docs.dripemails.org',
    'http://dripemails.org',  # For development/testing
    'http://localhost',
    'http://127.0.0.1',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    
    # Local apps
    'core.apps.CoreConfig',
    'campaigns.apps.CampaignsConfig',
    'subscribers.apps.SubscribersConfig',
    'analytics.apps.AnalyticsConfig',
    'gmail.apps.GmailConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Add locale middleware for i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'dripemails.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.current_year',
                'core.context_processors.site_detection',
            ],
        },
    },
]

WSGI_APPLICATION = 'dripemails.wsgi.application'

# Database Configuration
# PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'dripemails'),
        'USER': os.environ.get('DB_USER', 'dripemails'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'dripemails'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Available languages
from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian')),
    ('pt', _('Portuguese')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('ru', _('Russian')),
    ('zh-hans', _('Chinese (Simplified)')),
    ('zh-hant', _('Chinese (Traditional)')),
    ('ja', _('Japanese')),
    ('ko', _('Korean')),
    ('ar', _('Arabic')),
    ('hi', _('Hindi')),
    ('tr', _('Turkish')),
    ('pl', _('Polish')),
    ('nl', _('Dutch')),
    ('sv', _('Swedish')),
    ('da', _('Danish')),
    ('no', _('Norwegian')),
    ('fi', _('Finnish')),
    ('cs', _('Czech')),
    ('ro', _('Romanian')),
    ('hu', _('Hungarian')),
    ('el', _('Greek')),
    ('he', _('Hebrew')),
    ('th', _('Thai')),
    ('vi', _('Vietnamese')),
    ('id', _('Indonesian')),
    ('ms', _('Malay')),
    ('uk', _('Ukrainian')),
    ('bg', _('Bulgarian')),
    ('hr', _('Croatian')),
    ('sr', _('Serbian')),
    ('sk', _('Slovak')),
    ('sl', _('Slovenian')),
    ('lt', _('Lithuanian')),
    ('lv', _('Latvian')),
    ('et', _('Estonian')),
    ('is', _('Icelandic')),
    ('ga', _('Irish')),
    ('mt', _('Maltese')),
    ('ca', _('Catalan')),
    ('eu', _('Basque')),
    ('gl', _('Galician')),
    ('cy', _('Welsh')),
    ('fa', _('Persian')),
    ('ur', _('Urdu')),
    ('bn', _('Bengali')),
    ('ta', _('Tamil')),
    ('te', _('Telugu')),
    ('mr', _('Marathi')),
    ('gu', _('Gujarati')),
    ('kn', _('Kannada')),
    ('ml', _('Malayalam')),
    ('pa', _('Punjabi')),
    ('ne', _('Nepali')),
    ('si', _('Sinhala')),
    ('my', _('Burmese')),
    ('km', _('Khmer')),
    ('lo', _('Lao')),
    ('ka', _('Georgian')),
    ('hy', _('Armenian')),
    ('az', _('Azerbaijani')),
    ('kk', _('Kazakh')),
    ('ky', _('Kyrgyz')),
    ('uz', _('Uzbek')),
    ('mn', _('Mongolian')),
    ('sw', _('Swahili')),
    ('af', _('Afrikaans')),
    ('zu', _('Zulu')),
    ('xh', _('Xhosa')),
    ('am', _('Amharic')),
    ('ha', _('Hausa')),
    ('yo', _('Yoruba')),
    ('ig', _('Igbo')),
    ('sn', _('Shona')),
    ('st', _('Sotho')),
    ('tn', _('Tswana')),
    ('ve', _('Venda')),
    ('ts', _('Tsonga')),
    ('ss', _('Swati')),
    ('nr', _('Ndebele')),
    ('nso', _('Northern Sotho')),
    ('eo', _('Esperanto')),
]

# Location of translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Allauth Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none' #was mandatory now none
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[DripEmails] '

# Login/Logout redirects
LOGIN_REDIRECT_URL = '/dashboard/'  # Redirect to dashboard after login
LOGOUT_REDIRECT_URL = '/'  # Redirect to home after logout

# Email Configuration
# Use Postfix for actual email delivery to external servers (Gmail, etc.)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))  # Use port 25 for Postfix
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'

# SMTP Authentication Configuration
# For production servers that require authentication, set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
# in your environment variables. If both are provided, Django will use them for authentication.
# If either is missing/empty, Django will attempt to send without authentication (useful for
# servers that don't require auth, but will fail if the server requires it).
_email_user = os.environ.get('EMAIL_HOST_USER', '').strip()
_email_password = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()

# Set credentials if both are provided
if _email_user and _email_password:
    EMAIL_HOST_USER = _email_user
    EMAIL_HOST_PASSWORD = _email_password
else:
    # If credentials are not provided, set to None (Django will skip authentication)
    # NOTE: This will fail if your SMTP server requires authentication!
    # Make sure to set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in your .env file for production.
    EMAIL_HOST_USER = None
    EMAIL_HOST_PASSWORD = None

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'founders@dripemails.org')
DEFAULT_URL = os.environ.get('DEFAULT_URL', 'https://dripemails.org')

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core.authentication.BearerTokenAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://dripemails.org",
    "http://dripemails.org:8005",
    "https://www.dripemails.org",
    "https://dripemail.org",
    "https://web1.dripemail.org",
    "https://web.dripemail.org",
    "https://www.dripemail.org",
    "https://web.dripemails.org",
    "https://web1.dripemails.org",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Security Settings
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
#X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# HTTPONLY - Set to False only if you need JavaScript access to cookies (less secure)
# For most cases, True is recommended for security
SESSION_COOKIE_HTTPONLY = False
CSRF_COOKIE_HTTPONLY = False
# SameSite attribute - 'Lax' allows cookies in same-site requests (most common)
# 'None' requires Secure=True and allows cross-site cookies (for subdomains/APIs)
# 'Strict' is most secure but can break some redirect flows
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
# Cookie domain - None is most reliable for same-site
# Use '.dripemails.org' ONLY if you need cookies shared across subdomains (www, api, etc.)
# IMPORTANT: Setting domain to '.dripemails.org' can cause issues when accessing via 'dripemails.org' directly
# If you need subdomain sharing, ensure all access is via a subdomain (e.g., www.dripemails.org)
SESSION_COOKIE_DOMAIN = None  # Most reliable - use None unless you need subdomain sharing
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = '/'  # Explicitly set cookie path
SESSION_COOKIE_NAME = 'sessionid'  # Explicitly set cookie name (default, but being explicit)
SESSION_COOKIE_AGE = 3600000000  # hopefully doesn't expire soon
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# Save session on every request to ensure it persists
SESSION_SAVE_EVERY_REQUEST = True
# Save session on every request to ensure it persists (important for cache backend)
SESSION_SAVE_EVERY_REQUEST = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'campaigns': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Cache Configuration
# Note: Django's built-in RedisCache backend does NOT support CLIENT_CLASS
# CLIENT_CLASS is only for django-redis package, not django.core.cache.backends.redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            # Do NOT include CLIENT_CLASS here - it's not supported by Django's built-in Redis backend
        },
        'KEY_PREFIX': 'dripemails',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Use database for sessions (more reliable than cache)
# Cache backend requires Redis to be working perfectly, and session cookies can get lost
# Database backend is more reliable for session persistence
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# If you want to use cache backend later (requires Redis to be working):
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Performance optimizations
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Ollama Configuration for AI Email Generation (Production)
# For local Ollama (same server as Django), use: http://localhost:11434
# For remote Ollama server, set OLLAMA_BASE_URL in .env file
# Model options:
#   - llama3.2:1b (smallest, ~1.3GB RAM, fastest, good for limited memory)
#   - llama3.2:3b (balanced, ~2.0GB RAM, better quality)
#   - llama3.2:1b (small, ~1GB RAM, fast and efficient)
# See docs/ai/ollama_remote_setup.md for setup instructions
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')  # Default to smaller model for limited memory
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '300'))  # Timeout in seconds (default: 300 = 5 minutes)

# Gmail/Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://dripemails.org/api/gmail/callback/')

# Data Retention Policy (in days)
DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', '30'))

# Admin site customization
ADMIN_SITE_HEADER = "DripEmails Administration"
ADMIN_SITE_TITLE = "DripEmails Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to DripEmails Administration" 


# CSRF settings for language-prefixed URLs
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # Must be False for JavaScript to access
CSRF_USE_SESSIONS = False  # Use cookie-based CSRF tokens
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow CSRF token to work across language prefixes
CSRF_COOKIE_PATH = '/'  # Make CSRF cookie available for all paths including language prefixes