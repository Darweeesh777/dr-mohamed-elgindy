"""
Django settings for the Dr. Mohamed Elgindi law firm website.

Local values (secret key, debug flag, firm contact details) are read from
environment variables, optionally loaded from a `.env` file next to manage.py.
See `.env.example` for the full list.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Load KEY=VALUE lines from a .env file without overriding real env vars."""
    if not path.exists():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / '.env')


def env(key, default=''):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return env(key, str(default)).lower() in ('1', 'true', 'yes', 'on')


DEBUG = env_bool('DJANGO_DEBUG', True)

SECRET_KEY = env('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off.')
    SECRET_KEY = 'django-insecure-local-development-only'

ALLOWED_HOSTS = [h.strip() for h in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.ArabicDefaultMiddleware',  # Arabic for new visitors, then their saved choice
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# Arabic is the primary language; every public URL is prefixed (/ar/, /en/).

LANGUAGE_CODE = 'ar'
LANGUAGES = [
    ('ar', 'العربية'),
    ('en', 'English'),
]
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Uploaded files (Site photos). Local disk in development; on the live site this
# must be persistent storage (see README → Site photos), not the app's own disk.
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Email (console only; no real email is sent in development)

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# Firm details. Leave a value empty until the client supplies it; the site
# then shows a clearly marked placeholder instead of an invented value.

FIRM = {
    'whatsapp_number': env('FIRM_WHATSAPP_NUMBER'),   # international format, digits only, e.g. 20XXXXXXXXXX
    'phone': env('FIRM_PHONE'),
    'email': env('FIRM_EMAIL'),
    'address_ar': env('FIRM_ADDRESS_AR'),
    'address_en': env('FIRM_ADDRESS_EN'),
    'maps_url': env('FIRM_MAPS_URL'),
    'map_coords': env('FIRM_MAP_COORDS'),                # 'lat,lng' for the embedded map
    'google_business_url': env('FIRM_GOOGLE_BUSINESS_URL'),  # the firm's Google Business Profile link
    'hours_ar': env('FIRM_HOURS_AR'),
    'hours_en': env('FIRM_HOURS_EN'),
    'site_url': env('SITE_URL'),                      # e.g. https://example.com, used for canonical links
}

# Official social accounts supplied by the firm (tracking parameters removed).
# Order here is the display order; an empty URL hides that account.
FIRM_SOCIAL = [
    ('facebook', env('FIRM_FACEBOOK_URL', 'https://www.facebook.com/share/1BzhYdzhTy/')),
    ('tiktok', env('FIRM_TIKTOK_URL', 'https://www.tiktok.com/@dr.mohamedelgandy')),
    ('youtube', env('FIRM_YOUTUBE_URL', 'https://www.youtube.com/@drmohamedelgendy')),
]
