import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-secret-key-change-in-production-!@#$%')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1,.vercel.app', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',


    # Apps
    'apps.authentication',
    'apps.patients',
    'apps.etl',
    'apps.analytics',
    'apps.ml',
    'apps.reports',
    'apps.dashboard',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ETLRequestLoggingMiddleware',
    'core.middleware.AuditMiddleware',
    'core.middleware.RoleBasedAccessMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database (auto-detect: SQLite si no hay PostgreSQL configurado)
# Soporta DATABASE_URL (Render/Neon) o variables DB_* individuales
import sys, re
database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    import urllib.parse
    parsed = urllib.parse.urlparse(database_url)
    db_name = parsed.path.lstrip('/').split('?')[0]
    query_params = urllib.parse.parse_qs(parsed.query)
    sslmode = query_params.get('sslmode', ['require'])[0]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or '5432',
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=0, cast=int),
            'OPTIONS': {'sslmode': sslmode},
        }
    }
elif 'test' in sys.argv or not config('DB_HOST', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'ATOMIC_REQUESTS': True,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': config('DB_NAME', default='healthcare_etl'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=0, cast=int),
        }
    }

AUTH_USER_MODEL = 'authentication.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files (use /tmp/ on Vercel serverless since filesystem is read-only)
MEDIA_URL = '/media/'
_IS_VERCEL = bool(os.environ.get('VERCEL'))
MEDIA_ROOT = Path('/tmp/media') if _IS_VERCEL else (BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
_cors_from_env = config('CORS_ALLOWED_ORIGINS', default='')
_cors_extra = [o.strip() for o in _cors_from_env.split(',') if o.strip()] if _cors_from_env else []
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://localhost:3001',
] + _cors_extra
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://.*\.vercel\.app$',
    r'^https://.*\.onrender\.com$',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'authorization', 'content-type', 'x-csrftoken',
    'x-requested-with', 'accept', 'origin',
]

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.vercel.app',
    'https://*.onrender.com',
]
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'NON_FIELD_ERRORS_KEY': 'error',
    'COERCE_DECIMAL_TO_STRING': True,
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Bogota'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=True, cast=bool)
CELERY_BEAT_SCHEDULE = {
    'execute-scheduled-etl': {
        'task': 'apps.etl.tasks.execute_scheduled_etl',
        'schedule': 3600,
    },
    'retrain-ml-models': {
        'task': 'apps.ml.tasks.retrain_ml_models',
        'schedule': 86400,
    },
    'cleanup-old-logs': {
        'task': 'core.tasks.cleanup_old_logs',
        'schedule': 604800,
    },
}

# Logging — solo archivo si el filesystem es escribible (serverless-friendly)
_use_file_logging = False
_logs_dir = BASE_DIR / 'logs'
try:
    _logs_dir.mkdir(exist_ok=True)
    _use_file_logging = True
except OSError:
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        'etl': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ml': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

if _use_file_logging:
    LOGGING['handlers']['file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': _logs_dir / 'healthcare_etl.log',
        'maxBytes': 10485760,
        'backupCount': 10,
        'formatter': 'verbose',
    }
    LOGGING['handlers']['etl_file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': _logs_dir / 'etl.log',
        'maxBytes': 10485760,
        'backupCount': 10,
        'formatter': 'verbose',
    }
    LOGGING['loggers']['django']['handlers'].append('file')
    LOGGING['loggers']['etl']['handlers'].append('etl_file')
    LOGGING['loggers']['ml']['handlers'].append('file')

# Import/Export
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Swagger
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
}

# ETL Settings
ETL_UPLOAD_MAX_SIZE = config('ETL_UPLOAD_MAX_SIZE_MB', default=50, cast=int) * 1024 * 1024
ETL_CHUNK_SIZE = config('ETL_CHUNK_SIZE', default=500, cast=int)
ETL_DEFAULT_ENCODING = config('ETL_DEFAULT_ENCODING', default='utf-8')

# ML Settings
ML_RANDOM_STATE = config('ML_RANDOM_STATE', default=42, cast=int)
ML_TEST_SIZE = config('ML_TEST_SIZE', default=0.2, cast=float)
ML_CV_FOLDS = config('ML_CV_FOLDS', default=5, cast=int)
ML_MODEL_PATH = BASE_DIR / config('ML_MODEL_PATH', default='models/')

# Email
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = 'noreply@healthcare-etl.com'

# Site
SITE_NAME = 'Healthcare ETL Platform'
SITE_DESCRIPTION = 'Plataforma empresarial de gestión, análisis y ML para datos clínicos'
