"""
Django settings for webapps project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import hashlib
import os
import sys

from django.utils.translation import ugettext_lazy as _
from logging.handlers import SysLogHandler

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY SETTINGS

# SECURITY WARNING: don't run with debug turned on in production!
DEFAULT_SECRET_KEY_FOR_TESTING_ONLY = '9fk7v#1t(&%q0$o=apfeanjb8t5g8#og)etnwqs@f+!chw*v92'
DEFAULT_FERNET_KEY_FOR_TESTING_ONLY = 'sec8Q1_Za4bAjfFtEC9AvH6ctZ3hlEiEIGGNZPOBSlI='
DEFAULT_CAS_SALT_FOR_TESTING_ONLY = 'pt33-5exSbk7-Az85e77CZ-yUtrujsZ'

# Override this block in real environment
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-varda-cacher',
    }
}
ALLOWED_HOSTS = ['*']
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = DEFAULT_SECRET_KEY_FOR_TESTING_ONLY
STATIC_URL = '/static/'

DEFAULT_CACHE_INVALIDATION_TIME = 54000  # 15 hours
BASIC_AUTHENTICATION_LOGIN_INTERVAL_IN_SECONDS = 300  # 5 minutes
SESSION_COOKIE_AGE = 43200  # 12 hours
FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY', DEFAULT_FERNET_KEY_FOR_TESTING_ONLY)
OPETUSHALLITUS_ORGANISAATIO_OID = "1.2.246.562.10.00000000001"

# Application definition
# In order to preserve the content-types in the DB,
# always add new apps to the bottom of the list
INSTALLED_APPS = [
    'crispy_forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django_filters',
    'guardian',
    'rest_framework',
    'rest_framework_swagger',
    'simple_history',
    'varda.apps.VardaConfig',
    'django_celery_results',
    'django_celery_beat',
    'django_cas_ng',
    'rest_framework.authtoken',
    'log_request_id',
    'validate_cas_proxy_url',
    'corsheaders',
    'token_resolved',
    'django.contrib.postgres',
]

MIDDLEWARE = [
    'validate_cas_proxy_url.middleware.ValidateCASProxyURL',
    'log_request_id.middleware.RequestIDMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'token_resolved.middleware.AddTokenHeaderMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'webapps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
        ],
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

WSGI_APPLICATION = 'webapps.wsgi.application'


# https://github.com/ottoyiu/django-cors-headers/

# TODO: Remove this
# https://jira.eduuni.fi/browse/CSCVARDA-392
CORS_ORIGIN_ALLOW_ALL = True

# CORS_ORIGIN_WHITELIST = ('localhost:4200', )
# CORS_ORIGIN_REGEX_WHITELIST = (r'^(https://)?(\w+\.)?varda-db\.fi$', )


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

def get_test_db_name():
    md5 = hashlib.md5()
    md5.update(os.environ.get('BUILD_TAG', 'no-tag').encode('utf-8'))
    return md5.hexdigest()


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRESQL_DATABASE', 'varda_db'),
        'USER': os.getenv('POSTGRESQL_USER', 'varda_admin'),
        'PASSWORD': os.getenv('POSTGRESQL_PASSWORD', 'localhero'),
        'HOST': os.getenv('POSTGRESQL_SERVICE_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRESQL_SERVICE_PORT', '5432'),
        'TEST': {
            'NAME': get_test_db_name(),
        },
    }
}

TESTING = sys.argv[1:2] == ['test']


# These were added when django-guardian was added
# https://github.com/django-guardian/django-guardian

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
    'varda.cas.oppija_cas_views.OppijaCASBackend',  # Before CASBackend because has view check
    'django_cas_ng.backends.CASBackend',
)
ANONYMOUS_USER_NAME = "anonymous"


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

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


# Django logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(process)-5d %(thread)d [%(request_id)s] "%(request_host)s" %(name)-50s %(levelname)-8s %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(name)s %(levelname)s %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'syslog': {
            'level': 'INFO',
            'filters': ['require_debug_false', 'request_id'],
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_LOCAL1,
            'address': ['127.0.0.1', 1514],
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        },
        'mail_admins_security': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        }
    },
    'loggers': {
        '': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'gunicorn': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery.beat': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'INFO'
        },
        'django.request': {
            'level': 'ERROR',
            'handlers': ['mail_admins', 'syslog', 'console'],
            'propagate': False,
        },
        'django.security': {
            'level': 'WARNING',
            'handlers': ['mail_admins_security'],
            'propagate': False,
        },
        'django.server': {
            'level': 'ERROR',
            'handlers': ['mail_admins', 'syslog', 'console'],
            'propagate': False,
        },
        'webapps.celery': {
            'handlers': ['mail_admins', 'syslog', 'console'],
            'level': 'WARNING',
            'propagate': False,
        }
    }
}


"""
API-Throttling:
- 10/second was not enough for local tests -> HTTP/1.1 429 Too Many Requests,
  therefore disable throttling for tests:
"""
if 'test' in sys.argv:
    CACHES['default'] = {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }


# TODO:_Set the strict-throttles to very strict, after initial loading has been performed. This is important for security reasons!
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'varda.custom_auth.CustomBasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'webapps.api_throttles.BurstRateThrottle',
        'webapps.api_throttles.SustainedGetRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',
        'burst': '20/second',
        'sustained_get': '10000/day',
        'sustained_modify': '50000/day',
        'burst_strict': '5/second',
        'sustained_strict': '500/day'
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'PAGE_SIZE': 20,
    'HTML_SELECT_CUTOFF': 200
}


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

# Language set to english because in unit tests that is the assumed language
# (language selection impacts also the language of error codes)
# Browser's language selection overrides this

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ('fi', _('Finnish')),
    ('sv', _('Swedish')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

# STATIC_URL = '/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "rest_framework", "static"),
]


# Swagger (online API documentation)

SWAGGER_SETTINGS = {
    'VALIDATOR_URL': None,
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'

LOGIN_REDIRECT_URL = '/'
SITE_ID = 1

CRISPY_TEMPLATE_PACK = 'bootstrap3'


# Content-Secure Policy, Keep our policy as strict as possible
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", 'maxcdn.bootstrapcdn.com', 'fonts.gstatic.com', 'fonts.googleapis.com')
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", 'ajax.googleapis.com')
CSP_FONT_SRC = ("'self'", 'maxcdn.bootstrapcdn.com', 'fonts.gstatic.com', 'fonts.googleapis.com')
CSP_IMG_SRC = ("'self'", 'data:')


if "VARDA_ENVIRONMENT_TYPE" not in os.environ:
    # Celery configuration for local dev server. Override this block in real environment
    BROKER_BACKEND = 'memory'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


# Opintopolku. Override this block in real environment
OPINTOPOLKU_DOMAIN = 'https://virkailija.testiopintopolku.fi'
OPPIJA_OPINTOPOLKU_DOMAIN = 'https://testiopintopolku.fi'
PRODUCTION_ENV = False


# CAS-authentication (OPH autentikointipalvelu)
CAS_SERVER_URL = OPINTOPOLKU_DOMAIN + '/cas/'
CAS_CREATE_USER = True
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_VERSION = 3
CAS_RETRY_LOGIN = False

# CAS-oppija-authentication (OPH autentikointipalvelu) see cas_settings.py for mapping
OPPIJA_CAS_SERVER_URL = OPPIJA_OPINTOPOLKU_DOMAIN + '/cas-oppija/'
OPPIJA_CAS_CREATE_USER = True
OPPIJA_CAS_LOGIN_MSG = None
OPPIJA_CAS_LOGGED_MSG = None
OPPIJA_CAS_VERSION = 3
OPPIJA_CAS_RETRY_LOGIN = False
OPPIJA_CAS_APPLY_ATTRIBUTES_TO_USER = True

# Validation hash must be in header CAS_NEXT_HASH
CAS_ACCEPT_PROXY_URL_FROM_HEADER = 'CAS_NEXT'
CAS_SALT = os.environ.get('VARDA_SALT', DEFAULT_CAS_SALT_FOR_TESTING_ONLY)

# Time interval (in hours) of posting changed toimipaikka-data to Org.palvelu
ORG_PALVELU_CHANGE_INTERVAL_IN_HOURS = 24

"""
TODO: This does not currently work. Login fails with 403 forbidden.
if "VARDA_HOSTNAME" in os.environ:
    CAS_PROXY_CALLBACK = "https://" + os.environ["VARDA_HOSTNAME"] + "/accounts/callback"  # The full url to the callback view
"""

# Extend these default settings with optional settings_environment.py file
try:
    from .settings_environment import *  # noqa: F403,F401
except ModuleNotFoundError:
    pass
