import logging
import os
import subprocess
import sys
import time

from django import setup as django_setup
from django.conf import settings as django_settings
from django.db.utils import OperationalError


def sql_setup():
	# start SQL proxy in the background
	subprocess.Popen([
		'/cloudsql/cloud_sql_proxy',
		'--dir=/cloudsql',
		'-quiet',
		'-instances={db_instance}=tcp:5432'.format(
			db_instance=os.environ.get('DB_INSTANCE'))],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL)

	# configure Django to use SQL proxy
	django_settings.configure(
		DEBUG=True,
		DATABASES={
			'default': {
				'ENGINE': 'django.db.backends.mysql',
				'NAME': os.environ.get('DB_NAME'),
				'USER': os.environ.get('DB_USER'),
				'PASSWORD': os.environ.get('DB_PASSWORD'),
				'HOST': '127.0.0.1',
				'PORT': 5432,
			}
		},
		INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes'],
	)
	django_setup()


def get_submission(id, max_attempts=4, delay_attempt=4):
	"""
	Retry obtaining submissions when MySQL connection is not ready yet.
	"""

	from models import Submission

	for attempt in range(max_attempts):
		try:
			submission = Submission.objects.get(id=id)
			return submission
		except OperationalError:
			if attempt < max_attempts - 1:
				# Connection may not be ready yet, try again
				time.sleep(delay_attempt)
			else:
				raise


def get_logger(debug=False, warn=True, stdout=sys.stdout, stderr=sys.stderr, filename=None):
	"""
	Creates a logger which sends some messages to stdout and some messagese to stderr.

	Parameters
	----------
	debug : bool
		If True, print debug messages.

	warn : bool
		If False, ignore warning messages.

	filename: str
		Logs can additionally be written to this file

	Returns
	-------
	logging.Logger
		AnGinstance of a logger
	"""

	logger = logging.Logger(__name__ + '.get_logger.{0}_{1}'.format(debug, warn))
	logger.setLevel(logging.DEBUG if debug else logging.INFO)

	# clear handlers
	logger.handlers = []

	formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

	# debug and info messages
	handler = logging.StreamHandler(stdout)
	handler.setFormatter(formatter)
	handler.setLevel(logging.DEBUG)
	handler.addFilter(lambda record: record.levelno <= logging.INFO)
	logger.addHandler(handler)

	# error and warning messages
	handler = logging.StreamHandler(stderr)
	handler.setFormatter(formatter)
	handler.setLevel(logging.WARNING if warn else logging.ERROR)
	logger.addHandler(handler)

	if filename:
		# additionally store logs here
		handler = logging.FileHandler(filename)
		handler.setFormatter(formatter)
		handler.setLevel(logging.DEBUG)
		logger.addHandler(handler)

	return logger
