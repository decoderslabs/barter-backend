import os
import environ
from pathlib import Path

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'admin_interface',
    'colorfield',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'axes',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.users',
    'apps.offers',
    'apps.proposals',
    'apps.deals',
    'apps.drops',
    'apps.membership',
    'apps.ratings',
    'apps.notifications',
    'apps.payments',
    'apps.contracts',
    'apps.admin_panel',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'barter.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'barter.wsgi.application'

DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3', engine='django.db.backends.sqlite3')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'axes.backends.AxesStandaloneBackend',
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:8080',
    'http://127.0.0.1:3000',
])

CORS_ALLOW_CREDENTIALS = True

# Supabase Settings
SUPABASE_URL = env('SUPABASE_URL', default='')
SUPABASE_KEY = env('SUPABASE_KEY', default='')

# Razorpay Settings
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='')

# Stripe Settings
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# SendGrid Settings
SENDGRID_API_KEY = env('SENDGRID_API_KEY', default='')

# Firebase Settings
FIREBASE_CREDENTIALS_JSON = env('FIREBASE_CREDENTIALS_JSON', default='')

# Encryption key for sensitive data
ENCRYPTION_KEY = env('ENCRYPTION_KEY', default='')

# Sentry
SENTRY_DSN = env('SENTRY_DSN', default='')

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Admin Interface
ADMIN_INTERFACE_TITLE = 'Barter Admin'
ADMIN_INTERFACE_NAME = 'Barter'
ADMIN_INTERFACE_INDEX_TITLE = 'Welcome to Barter Admin Panel'
ADMIN_INTERFACE_LANGUAGE = 'en'
ADMIN_INTERFACE_SHOW_INDENTATION = False

# OTP for 2FA
OTP_TOTP_ISSUER = 'Barter'

# Swagger / OpenAPI
SPECTACULAR_SETTINGS = {
    'TITLE': 'Barter API',
    'DESCRIPTION': 'Backend API for the Barter influencer-brand collaboration platform.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'AUTHENTICATION': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'SECURITY': [{'jwtAuth': []}],
}

# Django Axes for login protection
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = None
AXES_LOCKOUT_CALLABLE = None
