"""
Django settings for webcdi project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.utils.translation import gettext_lazy as _
from databases import *
from email import *
import socket
from captcha import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

from django.utils.crypto import get_random_string

def generate_secret_key(fname):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    f = open(fname, 'w')
    f.write("SECRET_KEY = '%s'\n"%get_random_string(50, chars))

# SECURITY WARNING: keep the secret key used in production secret!
try:
    from secret_key import *
except ImportError:
    SETTINGS_DIR=os.path.abspath(os.path.dirname(__file__))
    generate_secret_key(os.path.join(SETTINGS_DIR, 'secret_key.py'))
    from secret_key import *

#SECRET_KEY = 'bt8n72d_ks+(7d-s&9%3g^b(m3g#_grs#ir!m-p5$^5se@fdsu'

# SECURITY WARNING: don't run with debug turned on in production!

#NOTE FROM BEN: I CHANGED DEBUG = False to DEBUG = True 
# DEBUG = False

DEBUG = bool(os.environ.get('DEBUG', False))
#DEBUG = True
TEMPLATE_DEBUG = False

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

ADMINS = (
    ('Alessandro Sanchez', 'sanchez7@stanford.edu'),
)

MANAGERS = ADMINS

ALLOWED_HOSTS = ['web-cdi-dev4.us-west-2.elasticbeanstalk.com','web-cdi-dev6.mfpemr5vcz.us-west-2.elasticbeanstalk.com','localhost', '127.0.0.1','52.32.108.131','webcdi-dev.us-west-2.elasticbeanstalk.com','webcdi-prod.us-west-2.elasticbeanstalk.com', 'webcdi.stanford.edu', 'webcdi-dev.stanford.edu', '.elb.amazonaws.com']

IPS_TO_ADD = ['webcdi-dev.us-west-2.elasticbeanstalk.com', 'webcdi-prod.us-west-2.elasticbeanstalk.com', 'webcdi.stanford.edu', socket.gethostname()]

NEW_IPS = set()

for IP in IPS_TO_ADD:
    for i in range(0,100):
    	NEW_IPS.add(socket.gethostbyname(IP))

for IP in list(NEW_IPS):
	ALLOWED_HOSTS.append(IP)

# Application definition

INSTALLED_APPS = (
    'researcher_UI', 
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'cdi_forms',
    'crispy_forms',
    'django_tables2',
    'bootstrap4',
    'bootstrap3',
    'form_utils',
    'registration',
    'supplementtut',
    'django.contrib.sites',
    'axes',
    'csvimport.app.CSVImportConf',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'localflavor',
    'django_countries',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'webcdi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'researcher_UI.context_processors.get_site_context',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webcdi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
CRISPY_TEMPLATE_PACK = 'bootstrap3'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

DATE_INPUT_FORMATS = (
    '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y',  # '2006-10-25', '10/25/2006', '10/25/06'
    '%d/%m/%Y', '%d/%m/%y',
    # '%b %d %Y', '%b %d, %Y',             # 'Oct 25 2006', 'Oct 25, 2006'
    # '%d %b %Y', '%d %b, %Y',             # '25 Oct 2006', '25 Oct, 2006'
    # '%B %d %Y', '%B %d, %Y',             # 'October 25 2006', 'October 25, 2006'
    # '%d %B %Y', '%d %B, %Y',             # '25 October 2006', '25 October, 2006'
)


REGISTRATION_SUPPLEMENT_CLASS = 'supplementtut.models.MyRegistrationSupplement'
ACCOUNT_ACTIVATION_DAYS = 3
REGISTRATION_OPEN = True

AXES_LOGIN_FAILURE_LIMIT = 4
# AXES_LOCKOUT_TEMPLATE
AXES_LOCKOUT_URL = '/lockout/'
# AXES_NEVER_LOCKOUT_WHITELIST
# AXES_IP_WHITELIST

if SITE_ID != 3:
    AXES_NUM_PROXIES = 1
    AXES_BEHIND_REVERSE_PROXY = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr-ca', _('French Quebec')),
    ('en-ca', _('Canadian English')),
    ('nl', _('Dutch')),
]


COUNTRIES_FIRST = [
    'US','CA',
]

if SITE_ID == 3: USER_ADMIN_EMAIL = 'henrymehta@hotmail.com'
else : USER_ADMIN_EMAIL = 'webcdi-contact@stanford.edu'

#CSRF_COOKIE_SECURE=False
#CSRF_TRUSTED_ORIGINS = ('.elasticbeanstalk.com',)