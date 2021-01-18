import os
import logging
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SITE_ID = 1
SECRET_KEY = os.environ.get('SECRET_KEY', '') or '\$t5(+2v272pm0ig76)ex1hgg-$s2%h@78xb#m*b^wz31fo_1bk'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = bool(os.environ.get('DEBUG', False))
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.sites',
	'django.contrib.flatpages',
	'teams.apps.TeamsConfig',
	'submissions.apps.SubmissionsConfig',
	'clic.apps.CLICConfig',
	'crispy_forms',
	'pagedown',
	'markdown_deux',
	'publications',
	'debug_toolbar',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.cache.UpdateCacheMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.cache.FetchFromCacheMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
	'django.middleware.gzip.GZipMiddleware',
]

if DEBUG:
	# Django Debug Toolbar
	# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
	# https://stackoverflow.com/questions/26898597/django-debug-toolbar-and-docker
	import socket
	INTERNAL_IPS = [socket.gethostbyname(socket.gethostname())[:-1] + '1']
	MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

ROOT_URLCONF = 'clic.urls'

CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_CLASS_CONVERTERS = {'clearablefileinput': 'filestyle'}

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [os.path.join(BASE_DIR, 'templates')],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
				'django.template.context_processors.media',
			],
		},
	},
]

WSGI_APPLICATION = 'clic.wsgi.application'

AUTH_USER_MODEL = 'teams.Team'
LOGIN_REDIRECT_URL = 'submit'
LOGOUT_REDIRECT_URL = 'submit'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': os.environ.get('DB_NAME'),
		'USER': os.environ.get('DB_USER'),
		'PASSWORD': os.environ.get('DB_PASSWORD'),
		'HOST': os.environ.get('DB_HOST'),
		'PORT': os.environ.get('DB_PORT', 3306),
	}
}


# Caching
# https://docs.djangoproject.com/en/2.2/topics/cache/#local-memory-caching
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 20 if DEBUG else 60
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
	}
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
MEDIA_URL = 'http://storage.googleapis.com/clic2021_public/'
STATIC_URL = '/static/' if DEBUG else 'http://storage.googleapis.com/clic2021_public/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'media'),)


# Google Cloud Storage
# https://django-storages.readthedocs.io/en/latest/backends/gcloud.html
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.environ.get('BUCKET_PUBLIC')
GS_BUCKET_SUBMISSIONS = os.environ.get('BUCKET_SUBMISSIONS')
GS_MAX_MEMORY_SIZE = 10000000
GS_BLOB_CHUNK_SIZE = 1048576


# Markdown
# https://github.com/trentm/django-markdown-deux
# https://github.com/timmyomahony/django-pagedown
PAGEDOWN_SHOW_PREVIEW = False
MARKDOWN_DEUX_STYLES = {
	'default': {
		'extras': {
			'code-friendly': None,
		},
		'safe_mode': False,
	}
}


# Sentry error tracking, requires environment variable SENTRY_DSN to be set
# https://docs.sentry.io/platforms/python/
def before_send(event, hint):
	# remove sensitive information
	del event['user']['ip_address']
	del event['user']['email']
	return event
sentry_sdk.init(
	integrations=[DjangoIntegration()],
	before_send=before_send,
	send_default_pii=True)
