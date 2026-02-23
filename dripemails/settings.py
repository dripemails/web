"""
Django settings for dripemails project.
"""
import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-default-key-for-dev'),
    DATABASE_URL=(str, f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"),
    EMAIL_BACKEND=(str, 'django.core.mail.backends.smtp.EmailBackend'),
    EMAIL_HOST=(str, 'localhost'),
    EMAIL_PORT=(int, 1025),  # Default to 1025 to match run_smtp_server default (avoids Postfix conflict)
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    EMAIL_USE_TLS=(bool, False),
    DEFAULT_FROM_EMAIL=(str, 'DripEmails <noreply@dripemails.org>'),
    FOUNDERS_EMAIL=(str, 'founders@dripemails.org'),
    SITE_URL=(str, 'http://localhost:8000'),
    DEFAULT_URL=(str, 'http://localhost:8000/'),
    CELERY_ENABLED=(str, ''),  # Empty string means auto-detect, 'True'/'False' to override
    CELERY_BROKER_URL=(str, 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=(str, 'django-db'),
    OLLAMA_BASE_URL=(str, 'http://localhost:11434'),
    OLLAMA_MODEL=(str, 'llama3.2:1b'),
    OLLAMA_TIMEOUT=(int, 300),  # 5 minutes timeout for AI generation
    # Gmail/Google OAuth Configuration
    GOOGLE_CLIENT_ID=(str, ''),
    GOOGLE_CLIENT_SECRET=(str, ''),
    GOOGLE_REDIRECT_URI=(str, 'https://dripemails.org/api/gmail/callback/'),
    DATA_RETENTION_DAYS=(int, 30),  # Number of days to retain email messages and send activity
    SHOW_ADDRESS_NAME_MODAL_NEW_ACCOUNTS=(bool, True),  # Show CAN-SPAM address modal for new accounts
    FOLLOW_UP_AFTER_ADDRESS_CAMPAIGN_ID=(str, ''),  # Optional: campaign UUID to send after address form
    FOLLOW_UP_AFTER_ADDRESS_EMAIL_ID=(str, ''),  # Optional: email template UUID for that follow-up
)

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.dripemails.org']

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
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'crispy_forms',
    'crispy_tailwind',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'django_celery_beat',  # Not using django-celery-beat - would downgrade Django to 4.2.25
    'django_celery_results',
    
    # Local apps
    'core.apps.CoreConfig',
    'campaigns',
    'subscribers',
    'analytics',
    'gmail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.RequestStorageMiddleware',
    'core.middleware.NoCacheAuthPagesMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Add locale middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.FrameAncestorsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Origins allowed to embed the site in an iframe (mobile wrapper, etc.)
FRAME_ANCESTORS_ALLOWED = [
    "'self'",
    'https://localhost:5173',
    'http://localhost:5173',
]

ROOT_URLCONF = 'dripemails.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.current_year',
                'core.context_processors.site_detection',
                'core.context_processors.agent',
            ],
            'loaders': [
                'core.template_loaders.AgentTemplateLoader',
                ('django.template.loaders.filesystem.Loader', [os.path.join(BASE_DIR, 'templates')]),
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'dripemails.wsgi.application'

# Database
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASE_URL')
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
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
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Django AllAuth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
# For development, make email verification optional; for production use 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'none' #was mandatory now none
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email settings
# For development, use console backend to avoid SMTP connection errors
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = env('EMAIL_BACKEND')

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
FOUNDERS_EMAIL = env('FOUNDERS_EMAIL', default='founders@dripemails.org')

# For local development on Windows, make authentication optional
# If EMAIL_HOST_USER is empty, Django won't use authentication
# This is useful when running a local SMTP server without auth
import sys
if sys.platform == 'win32' and DEBUG:
    # On Windows development, ensure empty credentials don't cause issues
    if not EMAIL_HOST_USER:
        EMAIL_HOST_USER = ''
    if not EMAIL_HOST_PASSWORD:
        EMAIL_HOST_PASSWORD = ''
    # Ensure we're using port 1025 for local SMTP server (matches run_smtp_server default)
    # This avoids conflicts with Postfix which typically runs on port 25
    if EMAIL_HOST == 'localhost':
        # If port is 587 or 25, switch to 1025 for local dev (avoids Postfix conflicts)
        if EMAIL_PORT in (587, 25):
            EMAIL_PORT = 1025
            EMAIL_USE_TLS = False
        # Otherwise keep the configured port

# Celery settings (optional - Redis not required)
# Celery is used for asynchronous email sending, but the app will fall back to
# synchronous sending if Redis/Celery is not available
import sys
_celery_enabled_env = env('CELERY_ENABLED', default='')
if not _celery_enabled_env or _celery_enabled_env.lower() in ('', 'auto', 'none'):
    # Auto-detect: Disable Celery on Windows when DEBUG=True (for easier development)
    # Enable Celery by default on Linux/macOS or when DEBUG=False
    CELERY_ENABLED = (sys.platform != 'win32' or not DEBUG)
else:
    # Convert string to boolean
    CELERY_ENABLED = _celery_enabled_env.lower() in ('true', '1', 'yes', 'on')

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'  # Not using django-celery-beat
# To use beat without django-celery-beat, you can set:
# CELERY_BEAT_SCHEDULER = 'celery.beat:PersistentScheduler'

# Note: On Windows development with DEBUG=True, Celery is disabled by default
# Email sending will be synchronous. For production or to enable Celery, set
# CELERY_ENABLED=True in your .env file and ensure Redis is running.

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://dripemails.org',
]

# REST Framework settings
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
}

# Site URL for absolute URLs
SITE_URL = env('SITE_URL')

# Ollama Configuration for AI Email Generation (Local Development)
# For local development, Ollama should be running on localhost
# To use a remote Ollama server, update OLLAMA_BASE_URL in .env file
# Model options:
#   - llama3.2:1b (smallest, ~1.3GB RAM, fastest, good for limited memory)
#   - llama3.2:3b (balanced, ~2.0GB RAM, better quality)
#   - llama3.2:1b (small, ~1GB RAM, fast and efficient)
# See docs/ai/ollama_remote_setup.md for setup instructions
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL')
OLLAMA_MODEL = env('OLLAMA_MODEL')
OLLAMA_TIMEOUT = env('OLLAMA_TIMEOUT')  # Timeout in seconds (default: 300 = 5 minutes)

# Data Retention Policy (in days)
DATA_RETENTION_DAYS = env('DATA_RETENTION_DAYS')

# Show CAN-SPAM address modal for new accounts
# If True, show modal when address/name missing. If False, users must edit on settings page.
SHOW_ADDRESS_NAME_MODAL_NEW_ACCOUNTS = env('SHOW_ADDRESS_NAME_MODAL_NEW_ACCOUNTS')

# Optional: send this campaign email to the user after they submit the address form (e.g. welcome/follow-up).
# Set to campaign UUID and email template UUID, or leave unset to disable.
FOLLOW_UP_AFTER_ADDRESS_CAMPAIGN_ID = env('FOLLOW_UP_AFTER_ADDRESS_CAMPAIGN_ID')
FOLLOW_UP_AFTER_ADDRESS_EMAIL_ID = env('FOLLOW_UP_AFTER_ADDRESS_EMAIL_ID')