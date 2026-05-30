"""
Django settings for gym_booking project.
"""

from pathlib import Path
from django.contrib.messages import constants as messages_constants
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ────── PRODUCTION SECURITY ──────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-+6#a(nmvmeoc8&!==5qi2bo9il%9)s$z9t(zg$4f0qjfre)mp7')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Only in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        "default-src": ("'self'",),
    }
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',')
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ─── Apps ───────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap5',   # already there ✅
    'core',                # already there ✅
]

# ─── Middleware ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← FOR STATIC FILES
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gym_booking.urls'

# ─── Templates ──────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],        # APP_DIRS=True handles core/templates/ automatically
        'APP_DIRS': True,  # ← MUST be True so Django finds your templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',   # ← ADDED (needed for debug toolbar & templates)
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gym_booking.wsgi.application'

# ─── Database ───────────────────────────────────────────────
# For production on Vercel, use PostgreSQL; for local, use SQLite
if config('DATABASE_URL', default=None):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=config('DATABASE_URL'), conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── Password Validation ────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ───────────────────────────────────
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'   # ← CHANGED: was 'UTC', now Philippine time (PHT)

USE_I18N = True
USE_TZ = True

# ─── Static Files ───────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For collectstatic
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'core', 'static'),
]

# WhiteNoise compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Auth Redirects ─────────────────────────────────────────
LOGIN_REDIRECT_URL = 'dashboard'   # already there ✅
LOGOUT_REDIRECT_URL = 'login'      # already there ✅
LOGIN_URL = 'login'                # already there ✅

# ─── Bootstrap Alert Colours ────────────────────────────────
# Maps Django message levels to Bootstrap CSS classes
# Without this, error messages show as "alert-error" (invalid Bootstrap class)
# With this, they correctly show as "alert-danger" (valid Bootstrap class)
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'secondary',
    messages_constants.INFO:    'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR:   'danger',   # ← KEY FIX: "error" → "danger"
}